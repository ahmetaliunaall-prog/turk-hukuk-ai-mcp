-- Yalnız geçici thaimcp test satırları; tüm değişiklikler ROLLBACK edilir.
begin;
do $$
declare actor uuid; id1 uuid; id2 uuid; r jsonb; n integer;
begin
  select id into actor from auth.users order by created_at limit 1;
  if actor is null then raise exception 'Canlı DB testi için mevcut Auth kullanıcısı gerekli';end if;
  insert into public.thaimcp_admins(user_id) values(actor) on conflict(user_id) do nothing;
  assert (select count(*)=3 from pg_class where relname in ('thaimcp_admins','thaimcp_api_keys','thaimcp_usage') and relrowsecurity),'RLS kapalı';
  assert not has_table_privilege('anon','public.thaimcp_api_keys','SELECT'),'Anon anahtar okuyabilir';
  assert not has_table_privilege('authenticated','public.thaimcp_admins','SELECT'),'Normal kullanıcı admin okuyabilir';
  assert not has_function_privilege('anon','public.thaimcp_access(text,text,text,text,uuid,uuid,boolean,timestamptz,text)','EXECUTE'),'RPC anon açık';
  r:=public.thaimcp_access(p_action=>'create',p_hash=>repeat('a',64),p_prefix=>'Abc',p_label=>'temporary-test',p_actor=>actor,p_client=>'sql-fixture');id1:=(r->>'id')::uuid;
  assert id1 is not null,'Admin oluşturamadı';
  r:=public.thaimcp_access(p_action=>'list',p_actor=>actor,p_client=>'sql-fixture');
  assert r ? 'keys' and not r::text like '%key_hash%','Liste hash sızdırıyor';
  r:=public.thaimcp_access(p_action=>'list',p_actor=>gen_random_uuid(),p_client=>'sql-fixture');assert r->>'error'='forbidden','Yetkisiz admin';
  r:=public.thaimcp_access(p_action=>'verify',p_hash=>repeat('b',64),p_client=>'sql-fixture');assert r->>'valid'='false','Geçersiz anahtar';
  r:=public.thaimcp_access(p_action=>'consume',p_hash=>repeat('a',64),p_client=>'sql-fixture');assert r->>'valid'='true','Geçerli anahtar';
  assert (select usage_count=1 and last_used_at is not null from public.thaimcp_api_keys where id=id1),'Kullanım sayacı';
  update public.thaimcp_api_keys set expires_at=now()-interval '1 minute' where id=id1;
  r:=public.thaimcp_access(p_action=>'verify',p_hash=>repeat('a',64),p_client=>'sql-fixture');assert r->>'valid'='false','Süresi dolmuş anahtar';
  update public.thaimcp_api_keys set expires_at=null,active=false where id=id1;
  r:=public.thaimcp_access(p_action=>'verify',p_hash=>repeat('a',64),p_client=>'sql-fixture');assert r->>'valid'='false','Pasif anahtar';
  r:=public.thaimcp_access(p_action=>'toggle',p_id=>id1,p_actor=>actor,p_active=>true,p_client=>'sql-fixture');assert r->>'ok'='true','Aktifleştirme';
  r:=public.thaimcp_access(p_action=>'rotate',p_id=>id1,p_actor=>actor,p_hash=>repeat('c',64),p_prefix=>'Def',p_label=>'temporary-rotated',p_client=>'sql-fixture');id2:=(r->>'id')::uuid;assert id2 is not null,'Yenileme';
  r:=public.thaimcp_access(p_action=>'verify',p_hash=>repeat('a',64),p_client=>'sql-fixture');assert r->>'valid'='false','Eski anahtar geçerli';
  r:=public.thaimcp_access(p_action=>'toggle',p_id=>id1,p_actor=>actor,p_active=>true,p_client=>'sql-fixture');assert r->>'error'='not_found','İptal edilmiş anahtar yeniden açıldı';
  r:=public.thaimcp_access(p_action=>'revoke',p_id=>id2,p_actor=>actor,p_client=>'sql-fixture');assert r->>'ok'='true','İptal';
  r:=public.thaimcp_access(p_action=>'verify',p_hash=>repeat('c',64),p_client=>'sql-fixture');assert r->>'valid'='false','İptal geçersiz';
  for n in 1..3 loop assert public.thaimcp_rate('sql-test-rate',3,60),'Erken rate limit';end loop;
  assert not public.thaimcp_rate('sql-test-rate',3,60),'Rate limit çalışmadı';
  begin
    insert into public.thaimcp_api_keys(key_hash,key_prefix,label,created_by) values(repeat('a',64),'Abc','duplicate',actor);
    raise exception 'Aynı hash tekrar oluşturuldu';
  exception when unique_violation then null;end;
end $$;
select 'PASS: RLS, grants, admin, create/list, hash secrecy, invalid/expired/inactive/revoked, rotate, usage, rate, uniqueness' as result;
rollback;

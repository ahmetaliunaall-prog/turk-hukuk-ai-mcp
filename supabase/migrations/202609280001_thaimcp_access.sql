-- Yalnız thaimcp_* nesneleri. Diğer uygulamaların şemalarına dokunmaz.
begin;
create table if not exists public.thaimcp_admins (
  user_id uuid primary key references auth.users(id), active boolean not null default true,
  created_at timestamptz not null default now()
);
create table if not exists public.thaimcp_api_keys (
  id uuid primary key default gen_random_uuid(), key_hash text unique not null check(key_hash ~ '^[0-9a-f]{64}$'),
  key_prefix text not null check(length(key_prefix)=3), label text not null check(length(label) between 1 and 128),
  active boolean not null default true, created_at timestamptz not null default now(),
  last_used_at timestamptz, expires_at timestamptz, usage_count bigint not null default 0,
  created_by uuid not null references auth.users(id), revoked_at timestamptz
);
create table if not exists public.thaimcp_usage (
  scope text not null, bucket timestamptz not null, count integer not null default 0,
  primary key(scope,bucket)
);
alter table public.thaimcp_admins enable row level security;
alter table public.thaimcp_api_keys enable row level security;
alter table public.thaimcp_usage enable row level security;
revoke all on public.thaimcp_admins,public.thaimcp_api_keys,public.thaimcp_usage from public,anon,authenticated;
grant select,insert,update,delete on public.thaimcp_admins,public.thaimcp_api_keys,public.thaimcp_usage to service_role;

create or replace function public.thaimcp_rate(p_scope text,p_limit integer,p_window integer)
returns boolean language plpgsql security invoker set search_path='' as $$
declare n integer; b timestamptz;
begin
  b:=to_timestamp(floor(extract(epoch from now())/p_window)*p_window);
  insert into public.thaimcp_usage(scope,bucket,count) values(p_scope,b,1)
  on conflict(scope,bucket) do update set count=public.thaimcp_usage.count+1 returning count into n;
  -- Bu projeye ait geçici sayaçlar, olay metni/IP/anahtar içermez.
  delete from public.thaimcp_usage where bucket<now()-interval '2 days';
  return n<=p_limit;
end $$;

create or replace function public.thaimcp_access(p_action text,p_hash text default '',p_prefix text default '',p_label text default '',p_id uuid default null,p_actor uuid default null,p_active boolean default true,p_expires timestamptz default null,p_client text default '')
returns jsonb language plpgsql security invoker set search_path='' as $$
declare k public.thaimcp_api_keys; out_rows jsonb; allowed boolean;
begin
  allowed:=public.thaimcp_rate('global',600,60);
  if not allowed then return jsonb_build_object('error','rate_limit');end if;
  allowed:=public.thaimcp_rate('client:'||p_client,30,60);
  if not allowed then return jsonb_build_object('error','rate_limit');end if;
  if p_action in ('verify','consume') then
    select * into k from public.thaimcp_api_keys where key_hash=p_hash for update;
    if k.id is null or not k.active or k.revoked_at is not null or (k.expires_at is not null and k.expires_at<=now()) then
      return jsonb_build_object('valid',false);
    end if;
    if p_action='consume' then
      allowed:=public.thaimcp_rate('key:'||k.id::text,10,60);
      if not allowed then return jsonb_build_object('error','rate_limit');end if;
      update public.thaimcp_api_keys set last_used_at=now(),usage_count=usage_count+1 where id=k.id;
    end if;
    return jsonb_build_object('valid',true);
  end if;
  if p_actor is null or not exists(select 1 from public.thaimcp_admins where user_id=p_actor and active) then
    return jsonb_build_object('error','forbidden');
  end if;
  if p_action='list' then
    select coalesce(jsonb_agg(jsonb_build_object('id',id,'key_prefix',key_prefix,'label',label,'active',active,'created_at',created_at,'last_used_at',last_used_at,'expires_at',expires_at,'usage_count',usage_count,'revoked_at',revoked_at) order by created_at desc),'[]'::jsonb)
    into out_rows from public.thaimcp_api_keys;
    return jsonb_build_object('keys',out_rows);
  elsif p_action in ('create','rotate') then
    if p_hash !~ '^[0-9a-f]{64}$' or length(p_prefix)<>3 or length(p_label) not between 1 and 128 or (p_expires is not null and p_expires<=now()) then
      return jsonb_build_object('error','invalid_input');
    end if;
    if p_action='rotate' then
      select * into k from public.thaimcp_api_keys where id=p_id for update;
      if k.id is null then return jsonb_build_object('error','not_found');end if;
      update public.thaimcp_api_keys set active=false,revoked_at=now() where id=p_id;
    end if;
    insert into public.thaimcp_api_keys(key_hash,key_prefix,label,created_by,expires_at) values(p_hash,p_prefix,p_label,p_actor,p_expires) returning id into p_id;
    return jsonb_build_object('id',p_id);
  elsif p_action='toggle' then
    update public.thaimcp_api_keys set active=p_active where id=p_id and revoked_at is null;
  elsif p_action='revoke' then
    update public.thaimcp_api_keys set active=false,revoked_at=now() where id=p_id;
  else return jsonb_build_object('error','invalid_action');
  end if;
  if not found then return jsonb_build_object('error','not_found');end if;
  return jsonb_build_object('ok',true);
end $$;
revoke all on function public.thaimcp_rate(text,integer,integer) from public,anon,authenticated;
revoke all on function public.thaimcp_access(text,text,text,text,uuid,uuid,boolean,timestamptz,text) from public,anon,authenticated;
grant execute on function public.thaimcp_rate(text,integer,integer) to service_role;
grant execute on function public.thaimcp_access(text,text,text,text,uuid,uuid,boolean,timestamptz,text) to service_role;
commit;

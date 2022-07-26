local ngx = ngx

local _M = {
    _VERSION = '0.1',
    TOKEN = os.getenv("TOKEN") and os.getenv("TOKEN") or "nsfl-proxy-token"
}


local function add_route_rule(id, service)
	-- get cache
	local iptables = ngx.shared.iptables
	-- if id already exist in cache, replace it.
	local old, flags = iptables:get(id)
	if old ~= nil then
		iptables:replace(id, service)
		ngx.log(ngx.WARN, "replace module: ", id, " service: ", service)
	else
		local succ, err, force = iptables:set(id, service)
		ngx.log(ngx.NOTICE, "add module: ", id, " service: ", service)
	end
	ngx.exit(ngx.HTTP_OK)
end


local function delete_route_rule(id)
	-- get cache
	local iptables = ngx.shared.iptables
	local service, flags = iptables:get(id)
	if service ~= nil then
		iptables:delete(id)
		ngx.log(ngx.NOTICE, "delete module: ", id, " service: ", service)
		ngx.say(ngx.HTTP_OK)
	else
		ngx.log(ngx.WARN, "not found module: ", id, " service.")
		ngx.exit(ngx.HTTP_NOT_FOUND)
	end
end


local function modify_route_rule(id, service)
	-- get cache
	local iptables = ngx.shared.iptables
	local old, flags = iptables:get(id)
	if old ~= nil then
		iptables:replace(id, service)
		ngx.log(ngx.WARN, "replace module: ", id, " old service: ", old, " with new service: ", service)
		ngx.say(ngx.HTTP_OK)
	else
		ngx.log(ngx.WARN, "not found module: ", id, " service.")
		ngx.exit(ngx.HTTP_NOT_FOUND)
	end
end


local function get_route_rule(id)
	-- get cache
	local iptables = ngx.shared.iptables
	local service, flags = iptables:get(id)
	if service ~= nil then
		ngx.say(service)
	else
		ngx.log(ngx.WARN, "not found module: ", id, " service.")
		ngx.exit(ngx.HTTP_NOT_FOUND)
	end
end


local function router_table()
	-- get rule <id, service>
	local method = ngx.req.get_method()
	local headers = ngx.req.get_headers()
	local id, service = headers["module-id"], headers["module-service"]
	local token = headers["token"]
	if token ~= _M.TOKEN then
		ngx.log(ngx.WARN, "Token not matched.")
		ngx.exit(ngx.HTTP_UNAUTHORIZED)
	end

	-- route according the method
	if method == "GET" then
		get_route_rule(id)
	elseif method == "POST" then
		add_route_rule(id, service)
	elseif method == "PUT" then
		modify_route_rule(id, service)
	elseif method == "DELETE" then
		delete_route_rule(id)
	else
		ngx.log(ngx.ERR, "Unknown method ", method)
		ngx.exit(ngx.HTTP_NOT_ALLOWED)
	end

end


function _M.start()
    router_table()
end


router_table()

local ngx = ngx
local dns = require "dns_resolver"


local function router()
	local iptables = ngx.shared.iptables
	-- index service from cache
	local headers = ngx.req.get_headers()
	local id = headers["module-id"]
	ngx.log(ngx.NOTICE, "try to get module-id: ", id, " service.")
	local service, flags = iptables:get(id)

	if service == nil then
		ngx.log(ngx.NOTICE, "Not found module: ", id, " service.")
		ngx.exit(ngx.HTTP_BAD_GATEWAY)
	else
		ngx.log(ngx.NOTICE, "Found module: ", id, " service: ", service)
		ngx.ctx.dest_service = service
	end

	dns.dns_resolve()

end


router()

local ngx = ngx
local resolver = require "resty.dns.resolver"

local _M = {
    _VERSION = '0.1'
}


local function init_dns()
	local iptables = ngx.shared.iptables
	local dns_server = iptables:get("DNS SERVER")

	local dns, err = resolver:new{
        nameservers = {dns_server, {dns_server, 53} },
        retrans = 5,  -- 5 retransmissions on receive timeout
        timeout = 2000,  -- 2 sec
        no_random = true, -- always start with first nameserver
    }
    if not dns then
        ngx.log(ngx.WARN, "failed to instantiate the resolver: ", err)
        return
    end

    return dns
end


local function resolve(dns, domian_name)

    local answers, err, tries = dns:query(domian_name, nil, {})

    if not answers then
        ngx.log(ngx.WARN, "failed to query the DNS server: ", err)
        ngx.log(ngx.NOTICE, "retry historie:\n  ", table.concat(tries, "\n  "))
        return
    end

    if answers.errcode then
        ngx.log(ngx.WARN, "server returned error code: ", answers.errcode,
                ": ", answers.errstr)
    end

    for i, ans in ipairs(answers) do
        ngx.log(ngx.NOTICE, ans.name, " ", ans.address or ans.cname,
                " type:", ans.type, " class:", ans.class,
                " ttl:", ans.ttl)
        if ans.address then
        	return ans.address
        end
    end

end


local function dns_resolve()
	-- body
    local service = ngx.ctx.dest_service
    local i, j = string.find(service, ":")
    local service_name = string.sub(service, 1, i-1)
    local port = string.sub(service, j+1)
    if string.find(service_name, "%d+.%d+.%d+.%d+") ~= nil then
        ngx.log(ngx.NOTICE, "no need to reslove dns, service ip:", service_name)
        return
    end

    local dns = init_dns()
    if dns ~= nil then
        local domian_name = service_name .. ".default.svc.cluster.local"

        local address = resolve(dns, domian_name)
        if address then
            ngx.ctx.dest_service = address..":"..port
        else
            ngx.log(ngx.WARN, "failed to reslove domian_name: ", domian_name)
        end

    else
        ngx.log(ngx.WARN, "dns server load failed.")
    end
end


return {
    dns_resolve = dns_resolve,
}

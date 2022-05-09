local _M = {
    _VERSION = '0.1'
}

local http=require("socket.http")
local ltn12 = require("ltn12")
local json = require('cjson')

local ngx = ngx
local iptables = ngx.shared.iptables

local response_body = {}
local job_scheduler_address = os.getenv("JOB_SCHEDULER_ADDRESS")


local function load_services()
	-- get exist module service
	if job_scheduler_address == nil then
		ngx.log(ngx.WARN, "no services to be load.")
		return
	end

  	local ok, code, response_headers, statusText  = http.request{
	  	url = "http://"..job_scheduler_address.."/api/v1/health",
	  	method = "GET",
	  	sink = ltn12.sink.table(response_body),
  	}

	if ok then
		local services = json.decode(response_body[1])
		-- parse the dict to iptable cache
		for key,val in pairs(services) do
			iptables:set(key, val)
			ngx.log(ngx.NOTICE, "load module: ", key, " service: ", val)
		end

	else
		ngx.log(ngx.WARN, "Load services failed: ", code, " ", statusText)
	end

end


local function read_dns_config()
	-- body
	local path = "/etc/resolv.conf"
	file = io.open(path, "r")
	io.input(file)
	local nameserver = io.read()
	dns_ip = string.sub(nameserver, string.find(nameserver, "%d+.%d+.%d+.%d+"))
	io.close(file)
	ngx.log(ngx.NOTICE, "DNS server: ", dns_ip)
	iptables:set("DNS SERVER", dns_ip)

end

local function start( ... )
	load_services()
	read_dns_config()
end


start()

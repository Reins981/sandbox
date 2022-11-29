#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
#NOTE: md5 algorithm - see ListValues.pm, Rows.pm
#FIXME: common code auslagern (zb. del_route, del_static_net ... ziemlich aehnlich
#FIXME: check ips / networks with ipaddr
"""
Barracuda Firewall Web Interface API.

Use the 'webui' class to interface with the barracuda firewall.
"""
import mechanize
import cookielib
import hashlib
import base64
import time
import urllib2
try:
    from bs4 import BeautifulSoup as bs
    #from modules.ext.BeautifulSoup.bs4 import BeautifulSoup as bs
except Exception,e:
    print "!!!! FIXME! --- BS4 NOT FOUND! %s"%e
try:
    import lxml.html.soupparser
except Exception,e:
    print "!!!! FIXME! --- LXML NOT FOUND! %s"%e


from QA_Logger import QA_Logger
LOG = QA_Logger(name='webui', loglevel=QA_Logger.L_DEBUG,
                print_stats_on_exit=False)


class QA_WebUI(object):
    """This class represents the web interface of the barracuda firewall.

    Basic usage:
    w = webui()
    w.open("10.17.70.223")
    w.login()
    w.add_route("0.0.0.0/0", "10.17.70.1")
    w.activate_net()
    """
    b = None   # browser
    r = None   # current request
    h = None   # current html
    usr = "admin"
    pwd = "admin"
    encpwd = None
    tree = None

    def __init__(self):
        self.b = mechanize.Browser()
        #self.b.set_proxies()
        self.b.set_cookiejar(cookielib.LWPCookieJar())
        self.b.set_handle_redirect(True)
        self.b.set_handle_referer(True)
        self.b.set_handle_robots(False)
        self.b.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    def _handle_response(self, r):
        """initializes self.h and self.tree, should be called everytime
        mechanize returns a response"""
        self.r = r
        self.h = self.r.read()
        if self.b.viewing_html():
            self.tree = lxml.html.soupparser.fromstring(self.h)
        else:
            self.tree = None

    def xpath(self, expr):
        """wrapper around the lxml xpath() method

        from the lxml docs:

        The return value types of XPath evaluations vary, depending on the
        XPath expression used:
        - True or False, when the XPath expression has a boolean result
        - a float, when the XPath expression has a numeric result (integer or
          float)
        - a 'smart' string (as described below), when the XPath expression has
          a string result.
        - a list of items, when the XPath expression has a list as result. The
          items may include Elements (also comments and processing
          instructions), strings and tuples. Text nodes and attributes in the
          result are returned as 'smart' string values. Namespace declarations
          are returned as tuples of strings: (prefix, URI).
        """
        if not self.b.viewing_html():
            raise Exception('Can only query XPath when viewing html')
        return self.tree.xpath(expr)

    def open(self, ip):
        """Open connection to webui box with given ip.

        This command establishes the initial connection to the webui box.
        Also the base url for further requests gets set.
        """
        self._handle_response(self.b.open("http://%s" % ip))

    def get(self, url):
        """Get the specified URL"""
        self._handle_response(self.b.open(url))

    def follow_link_by_id(self, id):
        self.get(self.xpath("id('%s')" % id)[0].attrib['href'])

    def content(self):
        """Returns the content of the last HTTP response."""
        return self.h

    def title(self):
        """Returns the HTML title of the last HTTP response."""
        return self.b.title()

    def url(self):
        """Returns the URL of the last HTTP response."""
        return self.b.geturl()

    def head(self):
        """Returns the HTML head section of the last HTTP response."""
        return bs(self.h).head()

    def body(self):
        """Returns the HTML body section of the last HTTP response."""
        return bs(self.h).body()

#Basic-> Status, Live Monitor, Firewall History, Thread Scan, Active Routes, User Activity, Alerts, Administration, Online Help Search
#Network-> IP Configuration, Routing, Interfaces, Interface Groups, Bridging, ARP, DHCP Server, Authoritative DNS, Proxy, Change Manager
#Firewall-> Firewall Rules, Network Objects, Service Objects, Connection Objects, User Objects, Time Objects, Intrusion Prevention, Captive Portal, Rule Tester, Settings
#VPN-> Site-to-Site Tunnels, Site-to-Site Settings, Client-To-Site VPN, PPTP, Active Clients, Certificates
#Users-> Guest Access, Local Services, External Services
#Logs-> Firewall Log, Network Log, VPN Log, Service Log, Authentication
#Advanced-> Backup, Energize Updates, Firmware Update, Appearance, Troubleshooting, Cloud Control, IPS Exceptions(, Expert Variables)
    def navigate(self, to="BASIC"):
        """Navigates to the given page.

        If no page is given the 'BASIC' page gets navigated to.
        e.g. navigate("IP Configuration")
        """
        # fetch el with id to
        # click it
        self._handle_response(self.b.follow_link(text=to))

    def activate_debug(self):
        """Activates verbose debug output.

        This output can be found on the box under /tmp/web_error_log (nginx)
        and /tmp/spinco (spincodaemon).
        FIXME: not implemented
        """
        #FIXME: touch /tmp/web.debug (nginx)
        #FIXME: killall spinco*, set perl env var, start
        #FIXME '/home/product/code/firmware/current/bin/spinco.pl 1'
        #FIXME: das ganze nohup!
        pass

    #NOTE: activate_net alters current page!
    def activate_net(self):
        """

        """
        # if http error try at least a second time
        try:
            self.navigate() #FIXME: workaround - after add_droute ... url is trunctated
            self.b.open(self.b.geturl()+"&activate_network_changes=") #FIXME: increase timeout
            #self.navigate("Change Manager")
            #self.b.select_form(nr=0)
            #self.b.forms().next().new_control("hidden", "activate_network_changes", {})
            #self._handle_response(self.b.submit())
            #NOTE: network activation is a background task which needs some time to finish
            time.sleep(20)
        except urllib2.HTTPError as e: #FIXME: check if e.code is bad gateway
            self.navigate()
            self.b.open(self.b.geturl()+"&activate_network_changes=") #FIXME: increase timeout
            time.sleep(20)

    def login(self, cred=None, retries=3, retrydelay=10):
        """Box login.

        Note: May take some time (few seconds to 2 minutes).
        """
        try:
            self.b.geturl()
        except:
            LOG.info("Please call open()/get() first ...")
            return

        if cred:
            self.usr = cred[0]
            self.pwd = cred[1]

        base_url = self.b.geturl()
        # trying several times because HTTP 502 errors happen a lot on login
        for i in range(retries + 1):
            try:
                self.b.select_form(nr=0)
                s = "%s%s" % (self.pwd, self.b.form.find_control(name="enc_key").value)
                s = s.replace('\r\n', '\n').replace('\r', '\n')
                pwd = hashlib.md5()
                pwd.update(s)
                self.encpwd = pwd.hexdigest()
                self.b.form["user"] = self.usr
                self.b.form["password_entry"] = ""
                self.b.form.find_control("password").readonly = False
                self.b.form["password"] = self.encpwd
                self.b.submit()
                self._handle_response(self.b.response())
                return
            except mechanize.HTTPError, e:
                LOG.warn("Got HTTP Error %d at login try #%d/%d, retrying (delay=+%ds)..." % (e.code, i + 1,retries,retrydelay))
                time.sleep(retrydelay)
                self.get(base_url)

        raise Exception('Could not successfully log in with %d tries.' % retries)

    def logout(self):
        """Box logout."""
        self.navigate("Log Off")

    def add_route(self, target, gw, pref=None):
        """Add a new static route."""
        ngw = gw.split(".")
        self.navigate("Routing")
        self.b.select_form(nr=0)
        self.b.form["UPDATE_new_routing_static_rte_target_net"] = target
        self.b.form["UPDATE_new_routing_static_rte_gateway__0"] = ngw[0]
        self.b.form["UPDATE_new_routing_static_rte_gateway__1"] = ngw[1]
        self.b.form["UPDATE_new_routing_static_rte_gateway__2"] = ngw[2]
        self.b.form["UPDATE_new_routing_static_rte_gateway__3"] = ngw[3]
        if pref:
            self.b.form["UPDATE_new_routing_static_rte_preference"] = str(pref)
        self.b.forms().next().new_control("hidden", "add_routing_static_rte_target_net", {"value": "Add"})
        self._handle_response(self.b.submit())

    def del_route(self, target, gateway, scope="global", scope_data=""):
        """Delete a static route."""
        self.navigate("Routing")
        self.b.select_form(nr=0)
        m = hashlib.md5()
        for v in ("routing_static_rte_target_net", "routing_static_rte_gateway", " ", target, " ", gateway, scope, scope_data):
            m.update(v)
        s = "md5%s" % base64.b64encode(m.digest())
        while s[-1] == "=": s = s[:-1]
        self.b.forms().next().new_control("hidden", "remove_routing_static_rte_target_net:%s" % s, {"value":"Remove"})
        self._handle_response(self.b.submit())

    #FIXME: only partial implementation
    def add_static_net(self, nic, nic_name, ip, mask, ping=True, dns=False, vpn=False, classification=None, gw=None, preference=None, secips=None):
        """Add a new static network."""
        self.navigate("IP Configuration")
        nip = ip.split(".")
        nmask = mask.split(".")

        # open "popup"
        url = self.b.geturl().split("&")
        for param in url:
            if param[:len("secondary_tab")] == "secondary_tab":
                url[url.index(param)] = "secondary_tab=add_static_nic"
                url.append("new_secondary_tab=network_ip_configuration")
        url.append("content_only=1")
        url.append("backup_life=0")
        newurl = "&".join(url)
        self._handle_response(self.b.open(newurl))
        
        self.b.select_form(nr=0)
        # nic, nic_name
        self.b.form["UPDATE_new_static_nic_iface"] = [nic] # p1, p2, ... (select)
        self.b.form["UPDATE_new_static_nic_name"] = nic_name # (text)
        # ip
        self.b.form["UPDATE_new_static_nic_ip__0"] = nip[0] # (octet)
        self.b.form["UPDATE_new_static_nic_ip__1"] = nip[1] # (octet)
        self.b.form["UPDATE_new_static_nic_ip__2"] = nip[2] # (octet)
        self.b.form["UPDATE_new_static_nic_ip__3"] = nip[3] # (octet)
        # mask
        self.b.form["UPDATE_new_static_nic_netmask__0"] = nmask[0] # (octet)
        self.b.form["UPDATE_new_static_nic_netmask__1"] = nmask[1] # (octet)
        self.b.form["UPDATE_new_static_nic_netmask__2"] = nmask[2] # (octet)
        self.b.form["UPDATE_new_static_nic_netmask__3"] = nmask[3] # (octet)
        # ping, dns, vpn
        self.b.form["UPDATE_new_static_nic_allow_ping"] = ["yes"] # (dropdown)
        #self.b.form["UPDATE_new_static_nic_allow_dns"] = ["no"] # (dropdown) #FIXME
        #self.b.form["UPDATE_new_static_nic_allow_vpn"] = ["no"] # (dropdown) #FIXME
        self.b.forms().next().new_control("hidden", "add_static_nic_name", {"secondary_scope_data":nic_name, "value":"Add"})
        self._handle_response(self.b.submit())

    def del_static_net(self, nic_name, ip):
        """Delete a static network."""
        self.navigate("IP Configuration")
        self.b.select_form(nr=0)
        m = hashlib.md5()
        for v in ("static_nic_name", "static_nic_ip", " ", nic_name, " ", ip, "global"):
            m.update(v)
        s = "md5%s" % base64.b64encode(m.digest())
        while s[-1] == "=": s = s[:-1]
        self.b.forms().next().new_control("hidden", "remove_static_nic_name:%s" % s, {"tied_scope_data":nic_name, "value":"Remove"})
        self._handle_response(self.b.submit())

    def enable_bcc(self, enable=False, usr=None, pwd=None):
        """Join or detach from BCC."""
        self.navigate("Cloud Control")
        self.b.select_form(nr=0)
        if enable:
            self.b.form["UPDATE_bcc_state"] = ["connected"] # (radio)
            self.b.form["UPDATE_bcc_username"] = usr # (text)
            self.b.form["UPDATE_bcc_password"] = pwd # (text)
        else:
            self.b.form["UPDATE_bcc_state"] = ["not_connected"] # (radio)
            self.b.forms().next().find_control("UPDATE_bcc_username").clear() # (text)
            self.b.forms().next().find_control("UPDATE_bcc_username").disabled = True
            self.b.forms().next().find_control("UPDATE_bcc_password").clear() # (text)
            self.b.forms().next().find_control("UPDATE_bcc_password").disabled = True
        self.b.forms().next().new_control("hidden", "save", {"value":"Save Changes"})
        self._handle_response(self.b.submit())

    def edit_mip(self, nic=None, ip=None, mask=None, ping=None, ntp=None):
        """Change settings for the management ip."""
        self.navigate("IP Configuration")
        self.b.select_form(nr=0)
        changed = False

        if nic:
            changed = True
            self.b.form["UPDATE_mgmt_iface"] = [nic] # (checkbox)
        if ip: 
            if not mask:
                LOG.info("Error: you have to supply the corresponding netmask")
                return
            changed = True
            nip = ip.split(".")
            nmask = mask.split(".")
            # ip
            self.b.form["UPDATE_system_ip__0"] = nip[0] # (octet)
            self.b.form["UPDATE_system_ip__1"] = nip[1] # (octet)
            self.b.form["UPDATE_system_ip__2"] = nip[2] # (octet)
            self.b.form["UPDATE_system_ip__3"] = nip[3] # (octet)
            # mask
            self.b.form["UPDATE_system_netmask__0"] = nmask[0] # (octet)
            self.b.form["UPDATE_system_netmask__1"] = nmask[1] # (octet)
            self.b.form["UPDATE_system_netmask__2"] = nmask[2] # (octet)
            self.b.form["UPDATE_system_netmask__3"] = nmask[3] # (octet)
        if ping:
            changed = True
            if ping == "yes": self.b.forms().next().find_control("UPDATE_system_ip_allow_ping").selected = True
            elif ping == "no": self.b.forms().next().find_control("UPDATE_system_ip_allow_ping").selected = False
            else: changed = False

        if ntp:
            changed = True
            self.b.form["UPDATE_system_ip_allow_ntp"] = [ntp] # (dropdown)
            if ntp == "yes": self.b.forms().next().find_control("UPDATE_system_ip_allow_ntp").selected = True
            elif ntp == "no": self.b.forms().next().find_control("UPDATE_system_ip_allow_ntp").selected = False
            else: changed = False

        if not changed:
            LOG.info("nothing changed ...")
            return
        self.b.forms().next().new_control("hidden", "save", {"value":"Save Changes"})
        self._handle_response(self.b.submit())
        if ip: self.login() #FIXME: notwendig?


if __name__=="__main__":
    w = QA_WebUI()
    w.open('10.17.67.153')
    print w.head()
    

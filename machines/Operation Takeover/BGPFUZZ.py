from scapy.all import *
load_contrib("bgp")
hdr = BGPHeader(type=1)
open_msg = BGPOpen(my_as=64512, bgp_id="my-ip", hold_time=180)
send(IP(dst="<target>")/TCP(dport=179)/hdr/open_msg)
#!/opt/local/bin/python2.7

# original code from
# http://pyusb.sourceforge.net/docs/1.0/tutorial.html
#
# adapted using code from
# http://code.rancidbacon.com/LearningAboutAtmelRZRAVEN
#
# author: Christophe VG

import usb.core
import usb.util
import sys
import time

# find our device
dev = usb.core.find(idVendor=0x03EB, idProduct=0x210A)

# was it found?
if dev is None:
	raise ValueError('Device not found')

# set the active configuration. With no arguments, the first
# configuration will be the active one
dev.set_configuration()

# get an endpoint instance
cfg = dev.get_active_configuration()

# dump information about configurations, interfaces and endpoints
print "*** dumping configuration/interface/endpoint info"
for cfg in dev:
    sys.stdout.write(str(cfg.bConfigurationValue) + '\n')
    for intf in cfg:
        sys.stdout.write('\t' + str(intf.bInterfaceNumber)  + \
                         ','  + str(intf.bAlternateSetting) + '\n')
        for ep in intf:
            sys.stdout.write('\t\t' + str(ep.bEndpointAddress) + '\n')

# output =
# 1
# 	0,0
# 		132			<--- read interface
# 		2				<--- write interface
# 		129			<--- to be discovered: is used below when waiting for joining mote

# endpoint configuration
epRead    = 0x84		# 132 = first interface
epWrite   = 0x02		#   2 = second interface
epControl = 0x81		# 129 = third interface

print "*** step 1: TODO: figure out what this does ;-)"
print "    if a USBError 60: Operation timed out happens here, reset the stick"
try:
	print dev.write(epWrite, [0x07, 0x03])
	print hex(dev.read(epRead, 1)[0])
except IndexError:
	print "Skip IndexError"

# output =
# 2
# 0x80

print "*** step 2: setting channel=11 pan id= 0xBABE (TODO: figure out...)"
try:
	# Channel: 11, Pan Id: 0xBABE                    
	print dev.write(epWrite, [0x22, 0x0B, 0xBE, 0xBA])
	print hex(dev.read(epRead, 1)[0])
except IndexError:
	print "Skip IndexError"

# output =
# 4
# 0x80
           
print "*** step 3: final step to turn on network (TODO: figure out...)"
print dev.write(epWrite, [0x23, 0x01])
print hex(dev.read(epRead, 1)[0])

print "*** network should be accessible now, turn on a mote"


def constructTextMsg(remoteAddress, text):
	MSG_COMMAND = 0x21
               
	packet = [MSG_COMMAND]

	# Note: Untested address manipulation.
	packet.extend((remoteAddress & 0xFF, remoteAddress >> 8))
	packet.extend((0x01, 0x01, 0x01)) # Unknown

	content = [0x00, 0x06] # Unknown
	content.append(len(text))
	content.extend([ord(c) for c in text]) # must be unicode array, not mixed

	packet.append(len(content))
	packet.extend(content)

	return packet

sentText = False
msgText = "Christophe was here ..."
msg = constructTextMsg(0x001B, msgText)

while 1:
	try:
		response = dev.read(epControl, 50)
	except usb.core.USBError:
		response = None
		pass

	if not response is None:
		print "*** received response on control(?) endpoint"
		print "    data = ", [hex(d) for d in response]

		if response[0] == 0x54:
			# TODO: process remote id also
			print "*** remote address 0x%02x%x joined." % (response[3], response[2])
			if not sentText:
				print "*** sending message: ", msgText
				print dev.write(epWrite, msg)
				print hex(dev.read(epRead, 1)[0])
				sentText = True

		# TODO: handle 0x55 as Leave?
		if response[0] == 0x55:
			print "*** received 0x55: leave ?"
                   
		# TODO: handle 0x53 as ??? (Message received?)
		if response[0] == 0x53:
			print "*** received 0x53: ack for txt msg ?"
			print dev.write(epWrite, [0x21, 0x1b, 0x00, 0x01, 0x01, 0x01, 0x02, 0x01, 0x1a])
			print hex(dev.read(epRead, 1)[0])

		if sentText:
			# Read temperature. Result is last two bytes of response.
			print "*** reading temperature"
			print dev.write(epWrite, [0x21, 0x1b, 0x00, 0x01, 0x01, 0x01, 0x03, 0x00, 0x0f, 0x00])
			print hex(dev.read(epRead, 1)[0])
		
	time.sleep(2)

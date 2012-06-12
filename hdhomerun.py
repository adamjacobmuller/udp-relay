#
# hdhomerun.py
#
# Copyright (c) 2011 Tako Schotanus <tako@codejive.org>.
#
# This library is free software; you can redistribute it and/or 
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.
# 
# As a special exception to the GNU Lesser General Public License,
# you may link, statically or dynamically, an application with a
# publicly distributed version of the Library to produce an
# executable file containing portions of the Library, and
# distribute that executable file under terms of your choice,
# without any of the additional requirements listed in clause 4 of
# the GNU Lesser General Public License.
# 
# By "a publicly distributed version of the Library", we mean
# either the unmodified Library as distributed by Silicondust, or a
# modified version of the Library that is distributed under the
# conditions defined in the GNU Lesser General Public License.
#

###################################################################################
# PS: Parts of the documentation in this file are copied from the C header files
# Copyright (c) 2006-2007 Silicondust USA Inc. <www.silicondust.com>.
# which are distributed under the LGPL as well, it's assumed the original copyright
# holders are okay with this.
###################################################################################

from ctypes import *
from ctypes import util
import sys, os

HDHOMERUN_DEVICE_TYPE_WILDCARD = 0xFFFFFFFF
HDHOMERUN_DEVICE_TYPE_TUNER = 0x00000001
HDHOMERUN_DEVICE_ID_WILDCARD = 0xFFFFFFFF

HDHOMERUN_STATUS_COLOR_NEUTRAL = 0xFFFFFFFF
HDHOMERUN_STATUS_COLOR_RED = 0xFFFF0000
HDHOMERUN_STATUS_COLOR_YELLOW = 0xFFFFFF00
HDHOMERUN_STATUS_COLOR_GREEN = 0xFF00C000

HDHOMERUN_CHANNELSCAN_PROGRAM_NORMAL = 0
HDHOMERUN_CHANNELSCAN_PROGRAM_NODATA = 1
HDHOMERUN_CHANNELSCAN_PROGRAM_CONTROL = 2
HDHOMERUN_CHANNELSCAN_PROGRAM_ENCRYPTED = 3

_c_bool = c_int32
        
class hdhomerun_discover_device_t(Structure):
    _fields_ = [
        ("ip_addr", c_uint32),
        ("device_type", c_uint32),
        ("device_id", c_uint32),
        ("tuner_count", c_ubyte)
    ]
    
    def connect(self, tuner = 0):
        return HdhrDevice(self.device_id, self.ip_addr, tuner)


class hdhomerun_tuner_vstatus_t(Structure):
    _fields_ = [
        ("vchannel", c_char * 32),
        ("name", c_char * 32),
        ("auth", c_char * 32),
        ("cci", c_char * 32),
        ("cgms", c_char * 32),
        ("not_subscribed", _c_bool),
        ("not_available", _c_bool),
        ("copy_protected", _c_bool),
    ]
   
class hdhomerun_tuner_status_t(Structure):
    _fields_ = [
        ("channel", c_char * 32),
        ("lock_str", c_char * 32),
        ("signal_present", _c_bool),
        ("lock_supported", _c_bool),
        ("lock_unsupported", _c_bool),
        ("signal_strength", c_int32),
        ("signal_to_noise_quality", c_int32),
        ("symbol_error_quality", c_int32),
        ("raw_bits_per_second", c_uint32),
        ("packets_per_second", c_uint32)
    ]
   
class hdhomerun_channelscan_program_t(Structure):
    _fields_ = [
        ("program_str", c_char * 64),
        ("program_number", c_ushort),
        ("virtual_major", c_ushort),
        ("virtual_minor", c_ushort),
        ("type", c_ushort),
        ("name", c_char * 32)
    ]

class hdhomerun_channelscan_result_t(Structure):
    _fields_ = [
        ("channel_str", c_char * 64),
        ("channelmap", c_uint32),
        ("frequency", c_uint32),
        ("status", hdhomerun_tuner_status_t),
        ("program_count", c_int32),
        ("programs", hdhomerun_channelscan_program_t * 64),
        ("transport_stream_id_detected", _c_bool),
        ("transport_stream_id", c_ushort)
    ]

class hdhomerun_plotsample_t(Structure):
    _fields_ = [
        ("real", c_ushort),
        ("imag", c_ushort)
    ]

#
# Low-level interface to libhdhomerun
#
class LibHdhr:
    def __init__(self):
        lib = self._libhdhr = cdll.LoadLibrary(util.find_library("hdhomerun"))
        # Discovery related functions
        LibHdhr._libfunc(lib.hdhomerun_discover_find_devices_custom, [ c_uint32, c_uint32, c_uint32, POINTER(hdhomerun_discover_device_t), c_int32 ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_discover_validate_device_id, [ c_uint32 ], _c_bool)
        # Device related functions
        LibHdhr._libfunc(lib.hdhomerun_device_create, [ c_uint32, c_uint32, c_uint32, c_void_p ], c_void_p)
        LibHdhr._libfunc(lib.hdhomerun_device_create_from_str, [ c_char_p, c_void_p ], c_void_p)
        LibHdhr._libfunc(lib.hdhomerun_device_destroy, [ c_void_p ])
        LibHdhr._libfunc(lib.hdhomerun_device_get_name, [ c_void_p ], c_char_p)
        LibHdhr._libfunc(lib.hdhomerun_device_get_device_id, [ c_void_p ], c_uint32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_device_ip, [ c_void_p ], c_uint32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_device_id_requested, [ c_void_p ], c_uint32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_device_ip_requested, [ c_void_p ], c_uint32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner, [ c_void_p ], c_uint32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_device, [ c_void_p, c_uint32, c_uint32 ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner, [ c_void_p, c_uint32 ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner_from_str, [ c_void_p, c_char_p ],c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_local_machine_addr, [ c_void_p ], c_uint32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_model_str, [ c_void_p ], c_char_p)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_status, [ c_void_p, POINTER(c_char_p), POINTER(hdhomerun_tuner_status_t) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_streaminfo, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_channel, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_channelmap, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_filter, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_program, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_target, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_lockkey_owner, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_ir_target, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_lineup_location, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner_channel, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner_channelmap, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner_filter, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner_program, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner_target, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_ir_target, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_set_lineup_location, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_version, [ c_void_p, POINTER(c_char_p), POINTER(c_uint32) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_supported, [ c_void_p, c_char_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_tuner_lockkey_request, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_tuner_lockkey_release, [ c_void_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_tuner_lockkey_force, [ c_void_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_tuner_lockkey_use_value, [ c_void_p, c_uint32 ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_wait_for_lock, [ c_void_p, POINTER(hdhomerun_tuner_status_t) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_channelscan_init, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_channelscan_advance, [ c_void_p, POINTER(hdhomerun_channelscan_result_t) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_channelscan_detect, [ c_void_p, POINTER(hdhomerun_channelscan_result_t) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_channelscan_get_progress, [ c_void_p ], c_ubyte)
        # Channel related functions
        LibHdhr._libfunc(lib.hdhomerun_channelmap_get_channelmap_scan_group, [ c_char_p ], c_char_p)

        LibHdhr._libfunc(lib.hdhomerun_device_set_tuner_vchannel, [ c_void_p, c_char_p ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_vchannel, [ c_void_p, POINTER(c_char_p) ], c_int32)
        LibHdhr._libfunc(lib.hdhomerun_device_get_tuner_vstatus, [ c_void_p, POINTER(c_char_p), POINTER(hdhomerun_tuner_vstatus_t) ], c_int32)
        
        
    @staticmethod
    def _libfunc(func, argtypes, restype = None):
        func.argtypes = argtypes
        func.restype = restype
        
    @staticmethod
    def _get_str_attr(func, device_p):
        p = pointer(c_char_p())
        res = func(device_p, p)
        if (res != 1):
            return (res, None)
        else:
            return (res, p.contents.value)

    #
    # Find devices.
    #
    # The device information is stored in caller-supplied array of hdhomerun_discover_device_t vars.
    # Multiple attempts are made to find devices.
    # Execution time is typically 400ms if max_count is not reached.
    #
    # Set target_ip to zero to auto-detect the IP address.
    # Set device_type to HDHOMERUN_DEVICE_TYPE_TUNER to detect HDHomeRun tuner devices.
    # Set device_id to HDHOMERUN_DEVICE_ID_WILDCARD to detect all device ids.
    #
    # Returns the number of devices found.
    # Retruns -1 on error.
    #
    def discover_find_devices_custom(self, target_ip, device_type, device_id, result_list = None, max_count = 64):
        result_list = result_list or (hdhomerun_discover_device_t * 64)()
        res = self._libhdhr.hdhomerun_discover_find_devices_custom(target_ip, device_type, device_id, pointer(result_list[0]), max_count)
        if (res < 0):
            return (res, None)
        else:
            return (res, result_list)
        
    #
    # Verify that the device ID given is valid.
    #
    # The device ID contains a self-check sequence that detects common user input errors including
    # single-digit errors and two digit transposition errors.
    #
    # Returns TRUE if valid.
    # Returns FALSE if not valid.
    #
    def discover_validate_device_id(self, device_id):
        return self._libhdhr.hdhomerun_discover_validate_device_id(device_id)

    #
    # uint32_t device_id = 32-bit device id of device. Set to HDHOMERUN_DEVICE_ID_WILDCARD to match any device ID.
    # uint32_t device_ip = IP address of device. Set to 0 to auto-detect.
    # unsigned int tuner = tuner index (0 or 1). Can be changed later by calling device_set_tuner().
    # struct hdhomerun_debug_t *dbg: Pointer to debug logging object. Optional.
    #
    # Returns a pointer to the newly created device object.
    #
    # When no longer needed, the socket should be destroyed by calling device_destroy().
    #
    def device_create(self, device_id = HDHOMERUN_DEVICE_ID_WILDCARD, device_ip = 0, tuner = 0, debug_t = None):
        return self._libhdhr.hdhomerun_device_create(device_id, device_ip, tuner, debug_t)

    #
    # The device_create_from_str function creates a device object from the given device_str.
    # The device_str parameter can be any of the following forms:
    #     <device id>
    #     <device id>-<tuner index>
    #     <ip address>
    # If the tuner index is not included in the device_str then it is set to zero. Use hdhomerun_device_set_tuner
    # or hdhomerun_device_set_tuner_from_str to set the tuner.
    #
    def device_create_from_str(self, device_str, debug_t = None):
        return self._libhdhr.hdhomerun_device_create_from_str(device_str, debug_t)

    #
    # Call when socket no longer needed
    #
    def device_destroy(self, device_p):
        self._libhdhr.hdhomerun_device_destroy(device_p)

    #
    # Get the device id, ip, or tuner of the device instance.
    #

    def device_get_name(self, device_p):
        return self._libhdhr.hdhomerun_device_get_name(device_p)

    def device_get_device_id(self, device_p):
        return self._libhdhr.hdhomerun_device_get_device_id(device_p)

    def device_get_device_ip(self, device_p):
        return self._libhdhr.hdhomerun_device_get_device_ip(device_p)

    def device_get_device_id_requested(self, device_p):
        return self._libhdhr.hdhomerun_device_get_device_id_requested(device_p)

    def device_get_device_ip_requested(self, device_p):
        return self._libhdhr.hdhomerun_device_get_device_ip_requested(device_p)

    def device_get_tuner(self, device_p):
        return self._libhdhr.hdhomerun_device_get_tuner(device_p)

    #
    # Get the device id, ip, or tuner of the device instance.
    #
    
    def device_set_device(self, device_p, device_id, device_ip):
        return self._libhdhr.hdhomerun_device_set_device(device_p, device_id, device_ip)

    def device_set_tuner(self, device_p, tuner):
        return self._libhdhr.hdhomerun_device_set_tuner(device_p, tuner)

    # The hdhomerun_device_set_tuner_from_str function sets the tuner from the given tuner_str.
    # The tuner_str parameter can be any of the following forms:
    #     <tuner index>
    #     /tuner<tuner index>
    def device_set_tuner_from_str(self, device_p, tuner_str):
        return self._libhdhr.hdhomerun_device_set_tuner_from_str(device_p, tuner_str)

    #
    # Get the local machine IP address used when communicating with the device.
    #
    # This function is useful for determining the IP address to use with set target commands.
    #
    # Returns 32-bit IP address with native endianness, or 0 on error.
    #
    def device_get_local_machine_addr(self, device_p):
        return self._libhdhr.hdhomerun_device_get_local_machine_addr(device_p)

    def device_get_model_str(self, device_p):
        return self._libhdhr.hdhomerun_device_get_model_str(device_p)

    #
    # Get operations.
    #
    # Returns a string with the information if the operation was successful.
    # Returns 0 if the operation was rejected.
    # Returns -1 if a communication error occurred.
    #
 
    def device_get_tuner_status(self, device_p, status = None):
        p = pointer(c_char_p())
        status = status or hdhomerun_tuner_status_t()
        res = self._libhdhr.hdhomerun_device_get_tuner_status(device_p, p, status)
        if (res != 1):
            return (res, None, None)
        else:
            return (res, p.contents.value, status)

    def device_get_tuner_streaminfo(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_streaminfo
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_tuner_channel(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_channel
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_tuner_vchannel(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_vchannel
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_tuner_vstatus(self, device_p, vstatus = None):
        p = pointer(c_char_p())
        vstatus = vstatus or hdhomerun_tuner_vstatus_t()
        res = self._libhdhr.hdhomerun_device_get_tuner_vstatus(device_p, p, vstatus)
        if (res != 1):
            return (res, None, None)
        else:
            return (res, p.contents.value, vstatus)

    def device_get_tuner_channelmap(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_channelmap
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_tuner_filter(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_filter
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_tuner_program(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_program
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_tuner_target(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_target
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_tuner_lockkey_owner(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_tuner_lockkey_owner
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_ir_target(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_ir_target
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_lineup_location(self, device_p):
        func = self._libhdhr.hdhomerun_device_get_lineup_location
        return LibHdhr._get_str_attr(func, device_p)

    def device_get_version(self, device_p):
        p = pointer(c_char_p())
        n = pointer(c_uint(0))
        res = self._libhdhr.hdhomerun_device_get_version(device_p, p, n)
        return (res, p.contents.value, n.contents.value)

    def device_get_supported(self, device_p, prefix):
        p = pointer(c_char_p())
        res = self._libhdhr.hdhomerun_device_get_supported(device_p, prefix, p)
        return (res, p.contents.value)

    #
    # Set operations.
    #
    # const char *<name> = String to send to device.
    #
    # Returns 1 if the operation was successful.
    # Returns 0 if the operation was rejected.
    # Returns -1 if a communication error occurred.
    #
 
    def device_set_tuner_channel(self, device_p, channel):
        return self._libhdhr.hdhomerun_device_set_tuner_channel(device_p, channel)
    
    def device_set_tuner_vchannel(self, device_p, vchannel):
        return self._libhdhr.hdhomerun_device_set_tuner_vchannel(device_p, vchannel)

    def device_set_tuner_channelmap(self, device_p, channelmap):
        return self._libhdhr.hdhomerun_device_set_tuner_channelmap(device_p, channelmap)

    def device_set_tuner_filter(self, device_p, filter):
        return self._libhdhr.hdhomerun_device_set_tuner_filter(device_p, filter)

    def device_set_tuner_program(self, device_p, program):
        return self._libhdhr.hdhomerun_device_set_tuner_program(device_p, program)

    def device_set_tuner_target(self, device_p, target):
        return self._libhdhr.hdhomerun_device_set_tuner_target(device_p, target)

    def device_set_ir_target(self, device_p, target):
        return self._libhdhr.hdhomerun_device_set_ir_target(device_p, target)

    def device_set_lineup_location(self, device_p, location):
        return self._libhdhr.hdhomerun_device_set_lineup_location(device_p, location)
        
        
    #
    # Tuner locking.
    #
    # The hdhomerun_device_tuner_lockkey_request function is used to obtain a lock
    # or to verify that the hdhomerun_device object still holds the lock.
    # Returns 1 if the lock request was successful and the lock was obtained.
    # Returns 0 if the lock request was rejected.
    # Returns -1 if a communication error occurs.
    #
    # The hdhomerun_device_tuner_lockkey_release function is used to release a
    # previously held lock. If locking is used then this function must be called
    # before destroying the hdhomerun_device object.
    #

    def device_tuner_lockkey_request(self, device_p):
        err = pointer(c_char_p())
        res = self._libhdhr.hdhomerun_device_tuner_lockkey_request(device_p, err)
        return (res, err.contents.value)

    def device_tuner_lockkey_release(self, device_p):
        return self._libhdhr.hdhomerun_device_tuner_lockkey_release(device_p)

    def device_tuner_lockkey_force(self, device_p):
        return self._libhdhr.hdhomerun_device_tuner_lockkey_force(device_p)

    #
    # Intended only for non persistent connections; eg, hdhomerun_config.
    #
    def device_tuner_lockkey_use_value(self, device_p, lockkey):
        return self._libhdhr.hdhomerun_device_tuner_lockkey_use_value(device_p, lockkey)

    #
    # Wait for tuner lock after channel change.
    #
    # The hdhomerun_device_wait_for_lock function is used to detect/wait for a lock vs no lock indication
    # after a channel change.
    #
    # It will return quickly if a lock is aquired.
    # It will return quickly if there is no signal detected.
    # Worst case it will time out after 1.5 seconds - the case where there is signal but no lock.
    #
    def device_wait_for_lock(self, device_p, status = None):
        status = status or hdhomerun_tuner_status_t()
        res = self._libhdhr.hdhomerun_device_wait_for_lock(device_p, status)
        if (res != 1):
            return (res, None)
        else:
            return (res, status)
    
    #
    # Channel scan API.
    #
    
    def device_channelscan_init(self, device_p, channelmap):
        return self._libhdhr.hdhomerun_device_channelscan_init(device_p, channelmap)
    
    def device_channelscan_advance(self, device_p, result = None):
        result = result or hdhomerun_channelscan_result_t()
        res = self._libhdhr.hdhomerun_device_channelscan_advance(device_p, result)
        if (res != 1):
            return (res, None)
        else:
            return (res, result)
    
    def device_channelscan_detect(self, device_p, result = None):
        result = result or hdhomerun_channelscan_result_t()
        res = self._libhdhr.hdhomerun_device_channelscan_detect(device_p, result)
        if (res != 1):
            return (res, None)
        else:
            return (res, result)
    
    def device_channelscan_get_progress(self, device_p):
        return self._libhdhr.hdhomerun_device_channelscan_get_progress(device_p)
    
    def channelmap_get_channelmap_scan_group(self, channelmap):
        return self._libhdhr.hdhomerun_channelmap_get_channelmap_scan_group(channelmap)
    

class HdhrDevice:
    def __init__(self, *args):
        self._lib = LibHdhr()
        self._locked = False
        if len(args) == 0:
            self._dev = self._lib.device_create()
        elif len(args) == 1 and isinstance(args[0], basestring):
            self._dev = self._lib.device_create_from_str(args[0])
        else:
            self._dev = self._lib.device_create(args[0], args[1], args[2])
            
        if self._dev == None:
            raise RuntimeError, 'could not create device'

    def __del__(self):
        if self._locked:
            try:
                self.tuner_lockkey_release()
            except:
                pass
        try:
            self._lib.device_destroy(self._dev)
        except:
            pass

    def _result(self, res):
        if isinstance(res, tuple):
            value = res[0]
            result = res[1]
        else:
            value = res
            result = res
        if value == 1:
            return result
        elif value == 0:
            raise RuntimeError, 'operation rejected'
        elif value == -1:
            raise RuntimeError, 'communication error'
        else:
            assert False
        
    def get_name(self):
        return self._lib.device_get_name(self._dev)

    def get_device_id(self):
        return self._lib.device_get_device_id(self._dev)

    def get_device_ip(self):
        return self._lib.device_get_device_ip(self._dev)

    def get_device_id_requested(self):
        return self._lib.device_get_device_id_requested(self._dev)

    def get_device_ip_requested(self):
        return self._lib.device_get_device_ip_requested(self._dev)

    def get_tuner(self):
        return self._lib.device_get_tuner(self._dev)

    def set_device(self, device_id, device_ip):
        return self._result(self._lib.device_set_device(self._dev, device_id, device_ip))

    def set_tuner(self, tuner):
        return self._result(self._lib.device_set_tuner(self._dev, tuner))

    def set_tuner_from_str(self, tuner_str):
        return self._result(self._lib.device_set_tuner_from_str(self._dev, tuner_str))

    def get_local_machine_addr(self):
        return self._lib.device_get_local_machine_addr(self._dev)

    def get_model_str(self):
        return self._lib.device_get_model_str(self._dev)

    def get_tuner_status(self, status = None):
        res = self._lib.device_get_tuner_status(self._dev, status)
        self._result(res[0])
        return res

    def get_tuner_streaminfo(self):
        return self._result(self._lib.device_get_tuner_streaminfo(self._dev))

    def get_tuner_channel(self):
        return self._result(self._lib.device_get_tuner_channel(self._dev))

    def get_tuner_channelmap(self):
        return self._result(self._lib.device_get_tuner_channelmap(self._dev))

    def get_tuner_filter(self):
        return self._result(self._lib.device_get_tuner_filter(self._dev))

    def get_tuner_program(self):
        return self._result(self._lib.device_get_tuner_program(self._dev))

    def get_tuner_target(self):
        return self._result(self._lib.device_get_tuner_target(self._dev))

    def get_tuner_lockkey_owner(self):
        return self._result(self._lib.device_get_tuner_lockkey_owner(self._dev))

    def get_ir_target(self):
        return self._result(self._lib.device_get_ir_target(self._dev))

    def get_lineup_location(self):
        return self._result(self._lib.device_get_lineup_location(self._dev))

    def get_version(self):
        return self._lib.device_get_version(self._dev)

    def get_supported(self, prefix):
        return self._lib.device_get_supported(self._dev, prefix)

    def set_tuner_channel(self, channel):
        return self._result(self._lib.device_set_tuner_channel(self._dev, channel))

    def set_tuner_channelmap(self, channelmap):
        return self._result(self._lib.device_set_tuner_channelmap(self._dev, channelmap))

    def set_tuner_filter(self, filter):
        return self._result(self._lib.device_set_tuner_filter(self._dev, filter))

    def set_tuner_program(self, program):
        return self._result(self._lib.device_set_tuner_program(self._dev, program))

    def set_tuner_target(self, target):
        return self._result(self._lib.device_set_tuner_target(self._dev, target))

    def set_ir_target(self, target):
        return self._result(self._lib.device_set_ir_target(self._dev, target))

    def set_lineup_location(self, location):
        return self._result(self._lib.device_set_lineup_location(self._dev, location))

    def tuner_lockkey_request(self):
        (res, err) = self._lib.device_tuner_lockkey_request(self._dev)
        if res == 1:
            self._locked = True
        return (res, err)

    def tuner_lockkey_release(self):
        res = self._result(self._lib.device_tuner_lockkey_release(self._dev))
        self._locked = False
        return res

    def tuner_lockkey_force(self):
        return self._result(self._lib.device_tuner_lockkey_force(self._dev))

    def tuner_lockkey_use_value(self, lockkey):
        return self._result(self._lib.device_tuner_lockkey_use_value(self._dev, lockkey))

    def wait_for_lock(self, status = None):
        return self._result(self._lib.device_wait_for_lock(self._dev, status))
    
    def channelscan_init(self, channelmap):
        return self._result(self._lib.device_channelscan_init(self._dev, channelmap))
    
    def channelscan_advance(self, result = None):
        (res, result) = self._lib.device_channelscan_advance(self._dev, result)
        if res == 0:
            result = None
        elif res == -1:
            raise RuntimeError, 'communication error'
        elif res != 1:
            assert False
        return result
    
    def channelscan_detect(self, result = None):
        (res, result) = self._lib.device_channelscan_detect(self._dev, result)
        if res == 0:
            result = None
        elif res == -1:
            raise RuntimeError, 'communication error'
        elif res != 1:
            assert False
        return result
    
    def channelscan_get_progress(self):
        res = self._lib.device_channelscan_get_progress(self._dev)
        if res == -1:
            raise RuntimeError, 'communication error'
        elif res < -1:
            assert False
        return res
    
    def channelmap_get_channelmap_scan_group(self, channelmap):
        return self._lib.channelmap_get_channelmap_scan_group(channelmap)

    def scan(self, callback, params = None):
        (res, err) = self.tuner_lockkey_request()
        if res != 1:
            return (res, err)
        scanresults = []
        self.set_tuner_target("none")
        chmap = self.get_tuner_channelmap()
        group = self.channelmap_get_channelmap_scan_group(chmap)
        if not not group:
            if self.channelscan_init(group) == 1:
                cont = True
                while cont:
                    scan = self.channelscan_advance()
                    if scan != None:
                        detres = self.channelscan_detect(scan)
                        if params != None:
                            scanres = callback(self, detres, scan, params)
                        else:
                            scanres = callback(self, detres, scan)
                        if (scanres != None):
                            scanresults += scanres
                        else:
                            cont = False
                    else:
                        cont = False
            else:
                return (0, "Could not initialize channel scan")
        else:
            return (0, "Unknown channel map")
        self.tuner_lockkey_release()
        return (1, scanresults)
    
            
class HdhrDiscovery:
    def __init__(self):
        self._lib = LibHdhr()
        self._devs = []
        self.refresh()
        
    def refresh(self):
        (res, devs) = self._lib.discover_find_devices_custom(0, HDHOMERUN_DEVICE_TYPE_TUNER, HDHOMERUN_DEVICE_ID_WILDCARD)
        if res == 1:
            for i in range(res):
                self._devs.append(devs[i])
    
    def devices(self):
        return self._devs
    
    def device(self, device_id):
        for dd in self._devs:
            if (device_id == dd.device_id):
                return dd
        return None
        
    def validate_device_id(self, device_id):
        return self._lib.discover_validate_device_id(device_id)


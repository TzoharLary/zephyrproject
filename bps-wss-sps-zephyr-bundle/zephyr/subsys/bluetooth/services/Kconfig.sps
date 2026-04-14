# Bluetooth GATT Scan Parameters service

# Copyright (c) 2026 The Zephyr Project
# SPDX-License-Identifier: Apache-2.0

menuconfig BT_SPS
	bool "GATT Scan Parameters service (SPS/SCPS)"
	depends on BT_PERIPHERAL
	help
	  Enable support for the Bluetooth Scan Parameters Service.
	  In Bluetooth SIG documents this service is commonly named ScPS.
	  Zephyr UUID macros and this implementation use SPS naming.

if BT_SPS

config BT_SPS_SCAN_REFRESH
	bool "Enable Scan Refresh characteristic"
	default y
	help
	  Enable the optional Scan Refresh characteristic (UUID 0x2A31)
	  with Notify property.

endif # BT_SPS

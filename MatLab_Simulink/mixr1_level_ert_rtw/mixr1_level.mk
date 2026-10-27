###########################################################################
## Makefile generated for component 'mixr1_level'. 
## 
## Makefile     : mixr1_level.mk
## Generated on : Mon Oct 26 20:43:42 2026
## Final product: $(RELATIVE_PATH_TO_ANCHOR)/mixr1_level.elf
## Product type : executable
## 
###########################################################################

###########################################################################
## MACROS
###########################################################################

# Macro Descriptions:
# PRODUCT_NAME            Name of the system to build
# MAKEFILE                Name of this makefile

PRODUCT_NAME              = mixr1_level
MAKEFILE                  = mixr1_level.mk
MATLAB_ROOT               = $(MATLAB_WORKSPACE)/C/Program_Files/MATLAB/R2026a
MATLAB_BIN                = $(MATLAB_WORKSPACE)/C/Program_Files/MATLAB/R2026a/bin
MATLAB_ARCH_BIN           = $(MATLAB_BIN)/win64
START_DIR                 = $(MATLAB_WORKSPACE)/C/Users/Cyril_Calo/Desktop/Research-SeBoCa-Test/MatLab_Simulink
SOLVER                    = 
SOLVER_OBJ                = 
CLASSIC_INTERFACE         = 0
TGT_FCN_LIB               = None
MODEL_HAS_DYNAMICALLY_LOADED_SFCNS = 0
RELATIVE_PATH_TO_ANCHOR   = ..
CUSTOM_C_FLAGS            = 
CUSTOM_CPP_FLAGS          = 
C_STANDARD_OPTS           = 
CPP_STANDARD_OPTS         = 

###########################################################################
## TOOLCHAIN SPECIFICATIONS
###########################################################################

# Toolchain Name:          GNU GCC RPIUtils
# Supported Version(s):    
# ToolchainInfo Version:   2026a
# Specification Revision:  1.0
# 

#-----------
# MACROS
#-----------

CCOUTPUTFLAG = --output_file=
LDOUTPUTFLAG = --output_file=

TOOLCHAIN_SRCS = 
TOOLCHAIN_INCS = 
TOOLCHAIN_LIBS = -lm -lrt -lpthread -ldl -lm -lstdc++ -lrt -lpthread -ldl

FORMAT_FOR_ECHO_CMD              = $(strip $(subst >,^>,\
	$(subst <,^<,\
	$(subst |,^|,\
	$(subst &,^&,\
	$(subst ",^",\
	$(subst ^,^^,\
	$1)))))))
FORMAT_FOR_ECHO_SH               = ""'$1'
SHELL_IS_CMD_EXE                := $(if $(findstring "$$SHELL",$(shell echo "$$SHELL")),1,)
FORMAT_FOR_ECHO                  = $(if $(SHELL_IS_CMD_EXE),$(FORMAT_FOR_ECHO_CMD),$(FORMAT_FOR_ECHO_SH))
HASH                             = \#
SEMICOLON                        = ;
UNESCAPE_SEMICOLONS              = $(subst \;,;,$1)
ADD_QUOTES                       = $(foreach aPath,$1,"$(aPath)")

#------------------------
# BUILD TOOL COMMANDS
#------------------------

# Assembler: GNU GCC RPIUtils Assembler
AS = as

# C Compiler: GNU GCC RPIUtils C Compiler
CC = gcc

# Linker: GNU GCC RPIUtils Linker
LD = gcc

# C++ Compiler: GNU GCC RPIUtils C++ Compiler
CPP = g++

# C++ Linker: GNU GCC RPIUtils C++ Linker
CPP_LD = g++

# Archiver: GNU GCC RPIUtils Archiver
AR = ar

# MEX Tool: MEX Tool
MEX_PATH = $(MATLAB_ARCH_BIN)
MEX = "$(MEX_PATH)/mex"

# Download: Download
DOWNLOAD =

# Execute: Execute
EXECUTE = $(PRODUCT)

# Builder: Make Tool
MAKE = make


#-------------------------
# Directives/Utilities
#-------------------------

ASDEBUG             = -g
AS_OUTPUT_FLAG      = -o
CDEBUG              = -g
C_OUTPUT_FLAG       = -o
LDDEBUG             = -g
OUTPUT_FLAG         = -o
CPPDEBUG            = -g
CPP_OUTPUT_FLAG     = -o
CPPLDDEBUG          = -g
OUTPUT_FLAG         = -o
ARDEBUG             =
STATICLIB_OUTPUT_FLAG =
MEX_DEBUG           = -g
RM                  =
ECHO                = echo
MV                  =
RUN                 =

#----------------------------------------
# "Faster Builds" Build Configuration
#----------------------------------------

MEX_CPPFLAGS         =
MEX_CPPLDFLAGS       =
MEX_CFLAGS           =
MEX_LDFLAGS          =



#---------------------------
# Model-Specific Options
#---------------------------

ASFLAGS = -c  $(ASFLAGS_ADDITIONAL) $(INCLUDES)

CFLAGS = -c -MMD -MP -MF"$(@:%.o=%.dep)" -MT"$@"   -O2  -DMW_NUM_CORES=$(shell nproc)  $(CUSTOM_C_FLAGS) -g

LDFLAGS = -Wl,--no-as-needed -g

SHAREDLIB_LDFLAGS = -shared  -Wl,--no-as-needed -g

CPPFLAGS = -c -MMD -MP -MF"$(@:%.o=%.dep)" -MT"$@"  -fpermissive   -O2  -DMW_NUM_CORES=$(shell nproc)  $(CUSTOM_CPP_FLAGS) -g

CPP_LDFLAGS = -Wl,--no-as-needed -g

CPP_SHAREDLIB_LDFLAGS = -shared  -Wl,--no-as-needed -g

ARFLAGS = -r

DOWNLOAD_FLAGS = 

EXECUTE_FLAGS = 

MAKE_FLAGS = -j$(($(nproc)+1)) -Otarget -f $(MAKEFILE)

###########################################################################
## OUTPUT INFO
###########################################################################

PRODUCT = $(RELATIVE_PATH_TO_ANCHOR)/mixr1_level.elf
PRODUCT_TYPE = "executable"
BUILD_TYPE = "Top-Level Standalone Executable"

###########################################################################
## INCLUDE PATHS
###########################################################################

INCLUDES_BUILDINFO = -I$(START_DIR) -I$(START_DIR)/mixr1_level_ert_rtw -I$(MATLAB_ROOT)/extern/include -I$(MATLAB_ROOT)/simulink/include -I$(MATLAB_ROOT)/rtw/c/src -I$(MATLAB_ROOT)/rtw/c/src/ext_mode/common -I$(MATLAB_ROOT)/rtw/c/ert -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/include -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src -I$(MATLAB_ROOT)/toolbox/coder/rtiostream/src -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/include -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/common -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/include -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/include -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/include -I$(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default -I$(MATLAB_ROOT)/toolbox/rpib/raspiML/include -I$(MATLAB_ROOT)/toolbox/coder/rtiostream/src/utils -I$(MATLAB_ROOT)/toolbox/target/codertarget/rtos/inc

INCLUDES = $(INCLUDES_BUILDINFO)

###########################################################################
## DEFINES
###########################################################################

DEFINES_ = -DXCP_ADDRESS_GRANULARITY=XCP_ADDRESS_GRANULARITY_BYTE -DCODERTARGET_XCP_DAQ_PACKED_MODE -DCODERTARGET_XCP_MAX_CONTIGUOUS_SAMPLES=2 -D__MW_TARGET_USE_HARDWARE_RESOURCES_H__
DEFINES_BUILD_ARGS = -DCLASSIC_INTERFACE=0 -DALLOCATIONFCN=0 -DTERMFCN=1 -DONESTEPFCN=1 -DMAT_FILE=0 -DMULTI_INSTANCE_CODE=0 -DEXT_MODE=1 -DINTEGER_CODE=0 -DMT=0
DEFINES_CUSTOM = 
DEFINES_OPTS = -DXCP_EXTMODE_SIMULATION_TIME_IN_TICKS -DXCP_MEM_BLOCK_1_SIZE=32 -DXCP_MEM_BLOCK_1_NUMBER=1 -DXCP_MEM_BLOCK_2_SIZE=56 -DXCP_MEM_BLOCK_2_NUMBER=1 -DXCP_MEM_BLOCK_3_SIZE=48 -DXCP_MEM_BLOCK_3_NUMBER=1 -DXCP_MEM_RESERVED_POOLS_TOTAL_SIZE=1000130 -DXCP_MEM_RESERVED_POOLS_NUMBER=2 -DXCP_MEM_DAQ_RESERVED_POOL_BLOCKS_NUMBER=3 -DXCP_MEM_DAQ_RESERVED_POOLS_NUMBER=1 -DXCP_MIN_EVENT_NO_RESERVED_POOL=1 -DXCP_MAX_CTO_SIZE=32 -DXCP_MAX_DTO_SIZE=65532 -DXCP_MAX_ODT_ENTRY_SIZE=255 -DEXTMODE_XCP_TRIGGER_SUPPORT -DXCP_TIMESTAMP_BASED_ON_SIMULATION_TIME -DON_TARGET_WAIT_FOR_START=1 -DXCP_DAQ_SUPPORT -DXCP_CALIBRATION_SUPPORT -DXCP_TIMESTAMP_SUPPORT -DXCP_SET_MTA_SUPPORT -DTID01EQ=0 -DXCP_EXTMODE_RUN_BACKGROUND_FLUSH
DEFINES_SKIPFORSIL = -D__linux__ -DARM_PROJECT -D_USE_TARGET_UDP_ -D_RUNONTARGETHARDWARE_BUILD_ -DSTACK_SIZE=200000 -DRT
DEFINES_STANDARD = -DMODEL=mixr1_level -DNUMST=1 -DNCSTATES=0 -DHAVESTDIO -DMODEL_HAS_DYNAMICALLY_LOADED_SFCNS=0

DEFINES = $(DEFINES_) $(DEFINES_BUILD_ARGS) $(DEFINES_CUSTOM) $(DEFINES_OPTS) $(DEFINES_SKIPFORSIL) $(DEFINES_STANDARD)

###########################################################################
## SOURCE FILES
###########################################################################

SRCS = $(START_DIR)/act_wrapper.c $(START_DIR)/tof_wrapper.c $(START_DIR)/VL53L4CD_api.c $(START_DIR)/platform.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_mode.c $(START_DIR)/mixr1_level_ert_rtw/mixr1_level.c $(START_DIR)/mixr1_level_ert_rtw/mixr1_level_data.c $(START_DIR)/mixr1_level_ert_rtw/rtGetInf.c $(START_DIR)/mixr1_level_ert_rtw/rtGetNaN.c $(START_DIR)/mixr1_level_ert_rtw/rt_nonfinite.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_common.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_classic_trigger.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_param_default_tcp.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp_standard.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp_daq.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp_calibration.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/xcp_fifo.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/xcp_transport.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/xcp_mem_default.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/xcp_drv_rtiostream.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/common/xcp_utils.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/xcp_frame_tcp.c $(MATLAB_ROOT)/toolbox/rpib/raspiML/src/MW_raspi_init.c $(MATLAB_ROOT)/toolbox/rpib/raspiML/src/periphs/MW_Pyserver_control.c $(MATLAB_ROOT)/toolbox/rpib/raspiML/src/linuxtimelogger/linuxTimeLogger.c $(MATLAB_ROOT)/rtw/c/src/ext_mode/common/rtiostream_interface.c $(MATLAB_ROOT)/toolbox/coder/rtiostream/src/rtiostreamtcpip/rtiostream_tcpip.c $(MATLAB_ROOT)/toolbox/coder/rtiostream/src/utils/rtiostream_utils.c $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/xcp_platform_default.c $(MATLAB_ROOT)/toolbox/target/codertarget/rtos/src/linuxinitialize.c

MAIN_SRC = $(START_DIR)/mixr1_level_ert_rtw/ert_main.c

ALL_SRCS = $(SRCS) $(MAIN_SRC)

###########################################################################
## OBJECTS
###########################################################################

OBJS = act_wrapper.c.o tof_wrapper.c.o VL53L4CD_api.c.o platform.c.o xcp_ext_mode.c.o mixr1_level.c.o mixr1_level_data.c.o rtGetInf.c.o rtGetNaN.c.o rt_nonfinite.c.o xcp_ext_common.c.o xcp_ext_classic_trigger.c.o xcp_ext_param_default_tcp.c.o xcp.c.o xcp_standard.c.o xcp_daq.c.o xcp_calibration.c.o xcp_fifo.c.o xcp_transport.c.o xcp_mem_default.c.o xcp_drv_rtiostream.c.o xcp_utils.c.o xcp_frame_tcp.c.o MW_raspi_init.c.o MW_Pyserver_control.c.o linuxTimeLogger.c.o rtiostream_interface.c.o rtiostream_tcpip.c.o rtiostream_utils.c.o xcp_platform_default.c.o linuxinitialize.c.o

MAIN_OBJ = ert_main.c.o

ALL_OBJS = $(OBJS) $(MAIN_OBJ)

###########################################################################
## PREBUILT OBJECT FILES
###########################################################################

PREBUILT_OBJS = 

###########################################################################
## LIBRARIES
###########################################################################

LIBS = $(LINUX_TARGET_LIBS_MACRO)

###########################################################################
## SYSTEM LIBRARIES
###########################################################################

SYSTEM_LIBS = 

###########################################################################
## ADDITIONAL TOOLCHAIN FLAGS
###########################################################################

#---------------
# C Compiler
#---------------

CFLAGS_SKIPFORSIL =  
CFLAGS_BASIC = $(DEFINES) $(INCLUDES)

CFLAGS += $(CFLAGS_SKIPFORSIL) $(CFLAGS_BASIC)

#-----------
# Linker
#-----------

LDFLAGS_ = -lwiringPi
LDFLAGS_SKIPFORSIL =  

LDFLAGS += $(LDFLAGS_) $(LDFLAGS_SKIPFORSIL)

#--------------------------
# Shared Library Linker
#--------------------------

SHAREDLIB_LDFLAGS_ = -lwiringPi
SHAREDLIB_LDFLAGS_SKIPFORSIL =  

SHAREDLIB_LDFLAGS += $(SHAREDLIB_LDFLAGS_) $(SHAREDLIB_LDFLAGS_SKIPFORSIL)

#-----------------
# C++ Compiler
#-----------------

CPPFLAGS_SKIPFORSIL =  
CPPFLAGS_BASIC = $(DEFINES) $(INCLUDES)

CPPFLAGS += $(CPPFLAGS_SKIPFORSIL) $(CPPFLAGS_BASIC)

#---------------
# C++ Linker
#---------------

CPP_LDFLAGS_ = -lwiringPi
CPP_LDFLAGS_SKIPFORSIL =  

CPP_LDFLAGS += $(CPP_LDFLAGS_) $(CPP_LDFLAGS_SKIPFORSIL)

#------------------------------
# C++ Shared Library Linker
#------------------------------

CPP_SHAREDLIB_LDFLAGS_ = -lwiringPi
CPP_SHAREDLIB_LDFLAGS_SKIPFORSIL =  

CPP_SHAREDLIB_LDFLAGS += $(CPP_SHAREDLIB_LDFLAGS_) $(CPP_SHAREDLIB_LDFLAGS_SKIPFORSIL)

###########################################################################
## INLINED COMMANDS
###########################################################################


DERIVED_SRCS = $(subst .o,.dep,$(OBJS))

build:

%.dep:



-include codertarget_assembly_flags.mk
-include *.dep


###########################################################################
## PHONY TARGETS
###########################################################################

.PHONY : all build buildobj clean info prebuild download execute


all : build
	echo $(call FORMAT_FOR_ECHO,### Successfully generated all binary outputs.)


build : prebuild $(PRODUCT)


buildobj : prebuild $(OBJS) $(PREBUILT_OBJS) $(LIBS)
	echo $(call FORMAT_FOR_ECHO,### Successfully generated all binary outputs.)


prebuild : 


download : $(PRODUCT)


execute : download
	echo $(call FORMAT_FOR_ECHO,### Invoking postbuild tool Execute ...)
	$(EXECUTE) $(EXECUTE_FLAGS)
	echo $(call FORMAT_FOR_ECHO,### Done invoking postbuild tool.)


###########################################################################
## FINAL TARGET
###########################################################################

#-------------------------------------------
# Create a standalone executable            
#-------------------------------------------

$(PRODUCT) : $(OBJS) $(PREBUILT_OBJS) $(LIBS) $(MAIN_OBJ)
	echo $(call FORMAT_FOR_ECHO,### Creating standalone executable "$(PRODUCT)" ...)
	$(LD) $(LDFLAGS) -o $(PRODUCT) $(OBJS) $(MAIN_OBJ) $(LIBS) $(SYSTEM_LIBS) $(TOOLCHAIN_LIBS)
	echo $(call FORMAT_FOR_ECHO,### Created: "$(PRODUCT)")


###########################################################################
## INTERMEDIATE TARGETS
###########################################################################

#---------------------
# SOURCE-TO-OBJECT
#---------------------

%.c.o : %.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : %.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : %.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(RELATIVE_PATH_TO_ANCHOR)/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(RELATIVE_PATH_TO_ANCHOR)/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(RELATIVE_PATH_TO_ANCHOR)/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(START_DIR)/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(START_DIR)/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(START_DIR)/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(START_DIR)/mixr1_level_ert_rtw/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(START_DIR)/mixr1_level_ert_rtw/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(START_DIR)/mixr1_level_ert_rtw/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/rtw/c/src/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/rtw/c/src/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/rtw/c/src/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/simulink/src/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/simulink/src/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/simulink/src/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/toolbox/simulink/blocks/src/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/toolbox/simulink/blocks/src/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/toolbox/simulink/blocks/src/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/common/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/common/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/common/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


%.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/%.c
	$(CC) $(CFLAGS) -o "$@" "$<"


%.cpp.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/%.cpp
	$(CPP) $(CPPFLAGS) -o "$@" "$<"


%.s.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/%.s
	$(AS) $(ASFLAGS) -o "$@" "$<"


act_wrapper.c.o : $(START_DIR)/act_wrapper.c
	$(CC) $(CFLAGS) -o "$@" "$<"


tof_wrapper.c.o : $(START_DIR)/tof_wrapper.c
	$(CC) $(CFLAGS) -o "$@" "$<"


VL53L4CD_api.c.o : $(START_DIR)/VL53L4CD_api.c
	$(CC) $(CFLAGS) -o "$@" "$<"


platform.c.o : $(START_DIR)/platform.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_ext_mode.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_mode.c
	$(CC) $(CFLAGS) -o "$@" "$<"


ert_main.c.o : $(START_DIR)/mixr1_level_ert_rtw/ert_main.c
	$(CC) $(CFLAGS) -o "$@" "$<"


mixr1_level.c.o : $(START_DIR)/mixr1_level_ert_rtw/mixr1_level.c
	$(CC) $(CFLAGS) -o "$@" "$<"


mixr1_level_data.c.o : $(START_DIR)/mixr1_level_ert_rtw/mixr1_level_data.c
	$(CC) $(CFLAGS) -o "$@" "$<"


rtGetInf.c.o : $(START_DIR)/mixr1_level_ert_rtw/rtGetInf.c
	$(CC) $(CFLAGS) -o "$@" "$<"


rtGetNaN.c.o : $(START_DIR)/mixr1_level_ert_rtw/rtGetNaN.c
	$(CC) $(CFLAGS) -o "$@" "$<"


rt_nonfinite.c.o : $(START_DIR)/mixr1_level_ert_rtw/rt_nonfinite.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_ext_common.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_common.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_ext_classic_trigger.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_classic_trigger.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_ext_param_default_tcp.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/ext_mode/src/xcp_ext_param_default_tcp.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_standard.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp_standard.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_daq.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp_daq.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_calibration.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/protocol/src/xcp_calibration.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_fifo.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/xcp_fifo.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_transport.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/xcp_transport.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_mem_default.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/xcp_mem_default.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_drv_rtiostream.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/xcp_drv_rtiostream.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_utils.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/common/xcp_utils.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_frame_tcp.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/transport/src/xcp_frame_tcp.c
	$(CC) $(CFLAGS) -o "$@" "$<"


MW_raspi_init.c.o : $(MATLAB_ROOT)/toolbox/rpib/raspiML/src/MW_raspi_init.c
	$(CC) $(CFLAGS) -o "$@" "$<"


MW_Pyserver_control.c.o : $(MATLAB_ROOT)/toolbox/rpib/raspiML/src/periphs/MW_Pyserver_control.c
	$(CC) $(CFLAGS) -o "$@" "$<"


linuxTimeLogger.c.o : $(MATLAB_ROOT)/toolbox/rpib/raspiML/src/linuxtimelogger/linuxTimeLogger.c
	$(CC) $(CFLAGS) -o "$@" "$<"


rtiostream_interface.c.o : $(MATLAB_ROOT)/rtw/c/src/ext_mode/common/rtiostream_interface.c
	$(CC) $(CFLAGS) -o "$@" "$<"


rtiostream_tcpip.c.o : $(MATLAB_ROOT)/toolbox/coder/rtiostream/src/rtiostreamtcpip/rtiostream_tcpip.c
	$(CC) $(CFLAGS) -o "$@" "$<"


rtiostream_utils.c.o : $(MATLAB_ROOT)/toolbox/coder/rtiostream/src/utils/rtiostream_utils.c
	$(CC) $(CFLAGS) -o "$@" "$<"


xcp_platform_default.c.o : $(MATLAB_ROOT)/toolbox/coder/xcp/src/target/server/platform/default/xcp_platform_default.c
	$(CC) $(CFLAGS) -o "$@" "$<"


linuxinitialize.c.o : $(MATLAB_ROOT)/toolbox/target/codertarget/rtos/src/linuxinitialize.c
	$(CC) $(CFLAGS) -o "$@" "$<"


###########################################################################
## DEPENDENCIES
###########################################################################

$(ALL_OBJS) : rtw_proj.tmw $(MAKEFILE)


###########################################################################
## MISCELLANEOUS TARGETS
###########################################################################

info : 
	echo $(call FORMAT_FOR_ECHO,### PRODUCT = $(PRODUCT))
	echo $(call FORMAT_FOR_ECHO,### PRODUCT_TYPE = $(PRODUCT_TYPE))
	echo $(call FORMAT_FOR_ECHO,### BUILD_TYPE = $(BUILD_TYPE))
	echo $(call FORMAT_FOR_ECHO,### INCLUDES = $(INCLUDES))
	echo $(call FORMAT_FOR_ECHO,### DEFINES = $(DEFINES))
	echo $(call FORMAT_FOR_ECHO,### ALL_SRCS = $(ALL_SRCS))
	echo $(call FORMAT_FOR_ECHO,### ALL_OBJS = $(ALL_OBJS))
	echo $(call FORMAT_FOR_ECHO,### LIBS = $(LIBS))
	echo $(call FORMAT_FOR_ECHO,### MODELREF_LIBS = $(MODELREF_LIBS))
	echo $(call FORMAT_FOR_ECHO,### SYSTEM_LIBS = $(SYSTEM_LIBS))
	echo $(call FORMAT_FOR_ECHO,### TOOLCHAIN_LIBS = $(TOOLCHAIN_LIBS))
	echo $(call FORMAT_FOR_ECHO,### ASFLAGS = $(ASFLAGS))
	echo $(call FORMAT_FOR_ECHO,### CFLAGS = $(CFLAGS))
	echo $(call FORMAT_FOR_ECHO,### LDFLAGS = $(LDFLAGS))
	echo $(call FORMAT_FOR_ECHO,### SHAREDLIB_LDFLAGS = $(SHAREDLIB_LDFLAGS))
	echo $(call FORMAT_FOR_ECHO,### CPPFLAGS = $(CPPFLAGS))
	echo $(call FORMAT_FOR_ECHO,### CPP_LDFLAGS = $(CPP_LDFLAGS))
	echo $(call FORMAT_FOR_ECHO,### CPP_SHAREDLIB_LDFLAGS = $(CPP_SHAREDLIB_LDFLAGS))
	echo $(call FORMAT_FOR_ECHO,### ARFLAGS = $(ARFLAGS))
	echo $(call FORMAT_FOR_ECHO,### MEX_CFLAGS = $(MEX_CFLAGS))
	echo $(call FORMAT_FOR_ECHO,### MEX_CPPFLAGS = $(MEX_CPPFLAGS))
	echo $(call FORMAT_FOR_ECHO,### MEX_LDFLAGS = $(MEX_LDFLAGS))
	echo $(call FORMAT_FOR_ECHO,### MEX_CPPLDFLAGS = $(MEX_CPPLDFLAGS))
	echo $(call FORMAT_FOR_ECHO,### DOWNLOAD_FLAGS = $(DOWNLOAD_FLAGS))
	echo $(call FORMAT_FOR_ECHO,### EXECUTE_FLAGS = $(EXECUTE_FLAGS))
	echo $(call FORMAT_FOR_ECHO,### MAKE_FLAGS = $(MAKE_FLAGS))


clean : 
	$(ECHO) "### Deleting all derived files ..."
	$(RM) $(PRODUCT)
	$(RM) $(ALL_OBJS)
	$(RM) *.c.dep
	$(RM) *.cpp.dep
	$(ECHO) "### Deleted all derived files."



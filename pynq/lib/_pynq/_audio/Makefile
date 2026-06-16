C_SRC += audio_adau1761.cpp \
	 i2cps.c \
	 uio.c
OBJSC += audio_adau1761.o \
	 i2cps.o \
	 uio.o

all:	
	$(CC) -fPIC -c -g3 -ggdb $(C_SRC) $(CFLAGS)
	$(CXX) -g3 -ggdb -shared -fPIC -rdynamic $(OBJSC) -Wl,--start-group $(LIBS) -Wl,--end-group -o libaudio.so $(CFLAGS) $(LDFLAGS)
	rm *.o

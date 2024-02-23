from psychopy import parallel

port = parallel.ParallelPort(address=0xDFF8)

try:
    port.setData(128)
except NotImplementedError:
    def setParallelData(code):
        if code > 0:
            print(f"TRIG {code} (Fake)")
            pass
else:
    port.setData(0)
    setParallelData = port.setData


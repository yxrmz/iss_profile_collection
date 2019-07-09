import numpy as np
import matplotlib.pyplot as plt

fin = open('FAstreamSettings.txt','r')

N = int(fin.readline().split(':')[1])
Gains = [int(x) for x in fin.readline().split(':')[1].split(',')]
Offsets = [int(x) for x in fin.readline().split(':')[1].split(',')]
FAdiv = (fin.readline().split(':')[1])
fin.readline()
Ranges = [int(x) for x in fin.readline().split(':')[1].split(',')]
FArate = float(fin.readline().split(':')[1])

def Range(val):
    if(val==1): r = 1
    if(val==2): r = 10
    if(val==4): r = 100
    if(val==8): r = 1000
    if(val==16): r = 100087
    return(r)

X = np.fromfile("FAstream.bin",dtype=int)
print(len(X))
A = []
B = []
C = []
D = []
T = []
Ra = Range(Ranges[0])
Rb = Range(Ranges[1])
Rc = Range(Ranges[2])
Rd = Range(Ranges[3])
dt = 1.0/FArate/1000.0

for i in range(0,len(X),4):
    A.append(Ra*((X[i]/37.0)-Offsets[0])/Gains[0])
    B.append(Rb*((X[i+1]/37.0)-Offsets[1])/Gains[1])
    C.append(Rc*((X[i+2]/37.0)-Offsets[2])/Gains[2])
    D.append(Rd*((X[i+3]/37.0)-Offsets[3])/Gains[3])
    T.append(i*dt/4.0)
plt.figure(figsize=(10,8))
plt.subplot(2,2,1)    
plt.plot(T,A)
plt.xlabel("Time (Sec)")
plt.ylabel("Ch.A (uA)")
plt.grid(True)

plt.subplot(2,2,2)    
plt.plot(T,B)
plt.xlabel("Time (Sec)")
plt.ylabel("Ch.B (uA)")
plt.grid(True)

plt.subplot(2,2,3)    
plt.plot(T,C)
plt.xlabel("Time (Sec)")
plt.ylabel("Ch.C (uA)")
plt.grid(True)

plt.subplot(2,2,4)    
plt.plot(T,D)
plt.xlabel("Time (Sec)")
plt.ylabel("Ch.D (uA)")
plt.grid(True)

plt.show()

    

    


import sys
a=open(sys.argv[1],'rb').read();b=open(sys.argv[2],'rb').read();gap=int(sys.argv[3]) if len(sys.argv)>3 else 16
d=[i for i in range(len(a)) if a[i]!=b[i]]
s=p=d[0];r=[]
for i in d[1:]:
    if i>p+gap: r.append((s,p));s=i
    p=i
r.append((s,p))
for s,e in r: print('%06X-%06X %6d'%(s,e,e-s+1))

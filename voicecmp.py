import wave, numpy as np

def load(p):
    with wave.open(p) as w:
        d=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float64)
        if w.getnchannels()==2: d=d.reshape(-1,2).mean(1)
        sr=w.getframerate()
    return d, sr

def f0_track(d, sr, fmin=60, fmax=350):
    win=int(0.04*sr); hop=int(0.02*sr); f0s=[]
    for i in range(0, len(d)-win, hop):
        x=d[i:i+win]
        if np.sqrt((x**2).mean())<200: continue
        x=x-x.mean()
        ac=np.correlate(x,x,'full')[win-1:]
        lo,hi=int(sr/fmax), int(sr/fmin)
        if hi>=len(ac): continue
        seg=ac[lo:hi]
        if seg.max()<=0: continue
        lag=lo+int(np.argmax(seg))
        if ac[lag]>0.3*ac[0]: f0s.append(sr/lag)
    return np.array(f0s)

def centroid(d, sr):
    win=int(0.04*sr); hop=int(0.02*sr); out=[]
    for i in range(0,len(d)-win,hop):
        x=d[i:i+win]
        if np.sqrt((x**2).mean())<200: continue
        X=np.abs(np.fft.rfft(x*np.hanning(win)))
        fr=np.fft.rfftfreq(win,1/sr)
        out.append((X*fr).sum()/X.sum())
    return np.median(out)

print(f"{'seg':5s} {'dur':>6s} {'F0':>7s} {'IQR':>6s} {'centroid':>9s} {'RMS':>7s}")
for i in range(6):
    d,sr=load(f"audio/seg{i}.wav")
    f0=f0_track(d,sr)
    rms=np.sqrt((d**2).mean())
    print(f"{i:<5d} {len(d)/sr:6.1f} {np.median(f0):7.1f} "
          f"{np.percentile(f0,75)-np.percentile(f0,25):6.1f} {centroid(d,sr):9.0f} {rms:7.0f}")

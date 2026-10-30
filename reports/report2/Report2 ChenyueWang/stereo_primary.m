function [y,info] = stereo_primary(x,fs,tauMs,bypass)
% STEREO_PRIMARY Rank-one Wiener estimate under equal uncorrelated noise.
% Uses real cross-power: intended for in-phase amplitude-panned sources.
% No cochlear weighting, post-scaling, HRTF or external helper dependency.
if nargin<4, bypass=false; end
L=512; H=128; N=size(x,1);
w=sqrt(0.5-0.5*cos(2*pi*(0:L-1)'/L));
xp=[zeros(L,2);x;zeros(L,2)];
out=zeros(size(xp)); normWin=zeros(size(xp,1),1);
P=zeros(L,2); C=zeros(L,1); a=exp(-H/(fs*tauMs/1000));
starts=1:H:(size(xp,1)-L+1); K=numel(starts);
info.icc=zeros(L/2+1,K); info.gain=info.icc;
for m=1:K
    idx=starts(m)+(0:L-1); X=fft(xp(idx,:).*w);
    P=a*P+(1-a)*abs(X).^2;
    C=a*C+(1-a)*real(X(:,1).*conj(X(:,2)));
    % Principal eigenvector of the real symmetric 2-by-2 covariance.
    delta=sqrt((P(:,1)-P(:,2)).^2+4*C.^2);
    hi=(sum(P,2)+delta)/2; lo=max(0,(sum(P,2)-delta)/2);
    theta=0.5*atan2(2*C,P(:,1)-P(:,2));
    v1=cos(theta); v2=sin(theta);
    gain=max(0,min(1,(hi-lo)./max(hi,1e-20)));
    primary=gain.*(v1.*X(:,1)+v2.*X(:,2));
    Y=[v1.*primary v2.*primary];
    if bypass, Y=X; end
    out(idx,:)=out(idx,:)+real(ifft(Y)).*w;
    normWin(idx)=normWin(idx)+w.^2;
    info.icc(:,m)=abs(C(1:L/2+1))./...
        max(sqrt(prod(P(1:L/2+1,:),2)),1e-20);
    info.gain(:,m)=gain(1:L/2+1);
end
y=out(L+(1:N),:)./max(normWin(L+(1:N)),1e-20);
info.t=((starts-1)+L/2-L)/fs; info.f=(0:L/2)'*fs/L;
end

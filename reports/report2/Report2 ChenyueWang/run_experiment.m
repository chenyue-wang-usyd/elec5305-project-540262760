function R = run_experiment()
% RUN_EXPERIMENT Reproducible parameter study; clean signal only scores output.
taus=[20 80 240]; pans=[1 0.4 1]; rhos=[0 0 0.8];
labels={'Centred / independent','Panned / independent','Centred / correlated'};
rows=zeros(45,7); k=0;
for scene=1:3
    for seed=1:5
        [x,s,fs,mask]=make_scene(5305+seed,pans(scene),rhos(scene));
        mid=repmat(mean(x,2),1,2);
        for q=1:numel(taus)
            y=stereo_primary(x,fs,taus(q)); k=k+1;
            rows(k,:)=[scene seed taus(q) score(s,x,mask) ...
                score(s,mid,mask) score(s,y,mask) ...
                10*log10(sum(y(mask,2).^2)/sum(y(mask,1).^2))];
        end
    end
end
R.table=array2table(rows,'VariableNames',...
    {'Scene','Seed','Tau_ms','Input_dB','Mid_dB','Primary_dB','Output_ICLD_dB'});
R.taus=taus; R.labels=labels;
[R.x,R.s,R.fs,R.mask]=make_scene(5306,0.4,0);
[R.y,R.info]=stereo_primary(R.x,R.fs,80);
identity=stereo_primary(R.x,R.fs,80,true);
R.identityError=max(abs(identity-R.x),[],'all');
assert(R.identityError<1e-12,'Overlap-add reconstruction failed.');
assert(all(isfinite(rows),'all'),'Nonfinite evaluation result.');
assert(max(abs(rows(:,4)))<1e-10,'Mixture SNR calibration failed.');
% Analytic model checks independent of the time-frequency implementation.
g=[1;0.4]; Q=2*(g*g')+0.3*eye(2);
[V,D]=eig(Q); [ev,j]=max(diag(D));
W=(ev-min(diag(D)))/ev*(V(:,j)*V(:,j)');
Wref=2*(g*g')/Q;
R.wienerError=max(abs(W-Wref),[],'all');
assert(R.wienerError<1e-12,'Wiener covariance identity failed.');
assert(isequal(size(R.y),size(R.x)),'Output length changed.');
writetable(R.table,'metrics.csv');
% Shared scale across reference, mixture and enhanced files, never per-file.
scale=0.95/max([abs(R.x(:));abs(R.s(:));abs(R.y(:))]);
audiowrite('reference.wav',scale*R.s,R.fs);
audiowrite('mixture.wav',scale*R.x,R.fs);
audiowrite('primary.wav',scale*R.y,R.fs);
R.audioScale=scale; save('experiment_results.mat','R');
end

function dB=score(s,y,mask)
% Scale-sensitive reconstruction SNR; no alignment or optimal gain fitting.
ref=s(mask,:); err=y(mask,:)-ref;
dB=10*log10(sum(ref.^2,'all')/sum(err.^2,'all'));
end

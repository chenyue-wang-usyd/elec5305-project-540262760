function report_figures(which,R)
% REPORT_FIGURES Compact figures for the Live Script and exported PDF.
if nargin<2, R=[]; end
f=figure('Color','w','Position',[100 100 820 440]);
set(f,'DefaultAxesFontSize',12,'DefaultTextFontSize',12);
switch which
    case 'pipeline'
        set(f,'Position',[100 100 820 260]); axis off;
        boxes={[.03 .57 .25 .24],'Stereo mixture';...
            [.375 .57 .25 .24],'Window + FFT';...
            [.72 .57 .25 .24],'Smoothed covariance';...
            [.72 .12 .25 .24],'Rank-one Wiener gain';...
            [.375 .12 .25 .24],'IFFT + overlap-add';...
            [.03 .12 .25 .24],'Primary stereo output'};
        for k=1:size(boxes,1)
            annotation('textbox',boxes{k,1},'String',boxes{k,2},...
                'HorizontalAlignment','center','VerticalAlignment','middle',...
                'BackgroundColor',[.92 .96 .99],'FontSize',12,'LineWidth',1);
        end
        annotation('arrow',[.28 .375],[.69 .69]);
        annotation('arrow',[.625 .72],[.69 .69]);
        annotation('arrow',[.845 .845],[.57 .36]);
        annotation('arrow',[.72 .625],[.24 .24]);
        annotation('arrow',[.375 .28],[.24 .24]);
    case 'maps'
        tiledlayout(2,1,'TileSpacing','compact','Padding','compact');
        nexttile; imagesc(R.info.t,R.info.f/1000,R.info.icc,[0 1]);
        axis xy; ylim([0 3]); xlim([0 6]); colorbar;
        ylabel('Frequency (kHz)'); title('Magnitude of smoothed real correlation');
        nexttile; imagesc(R.info.t,R.info.f/1000,R.info.gain,[0 1]);
        axis xy; ylim([0 3]); xlim([0 6]); colorbar;
        xlabel('Time (s)'); ylabel('Frequency (kHz)');
        title('Principal-component Wiener gain'); colormap parula;
    case 'study'
        tiledlayout(1,3,'TileSpacing','compact','Padding','compact');
        for scene=1:3
            nexttile; hold on; mu=zeros(1,3); sd=mu;
            for q=1:3
                sel=R.table.Scene==scene & R.table.Tau_ms==R.taus(q);
                v=R.table.Primary_dB(sel); mu(q)=mean(v); sd(q)=std(v);
            end
            errorbar(R.taus,mu,sd,'-o','LineWidth',1.7,'CapSize',9);
            b=mean(R.table.Mid_dB(R.table.Scene==scene));
            yline(b,'--','LineWidth',1.4); yline(0,':');
            set(gca,'XScale','log','XTick',R.taus); ylim([-1 13]);
            grid on; xlabel('Smoothing time (ms)');
            if scene==1, ylabel('Reconstruction SNR (dB)'); end
            title(strrep(R.labels{scene},' / ',newline));
            if scene==1, legend('Primary: mean +/- SD','Mid baseline',...
                    'Input','Location','northwest','FontSize',9); end
        end
    case 'spectra'
        tiledlayout(3,1,'TileSpacing','compact','Padding','compact');
        signals={R.s,R.x,R.y}; titles={'Reference','Mixture','Primary estimate'};
        L=512; H=128; w=0.5-0.5*cos(2*pi*(0:L-1)'/L);
        for k=1:3
            s=signals{k}(:,1); starts=1:H:numel(s)-L+1;
            frames=s((0:L-1)'+starts).*w; X=fft(frames);
            dB=20*log10(max(2*abs(X(1:L/2+1,:))/sum(w),1e-6));
            nexttile; imagesc((starts-1+L/2)/R.fs,(0:L/2)*R.fs/L/1000,dB,[-70 -15]);
            axis xy; ylim([0 3]); ylabel('kHz'); title(titles{k});
            c=colorbar; c.Label.String='dB re 1';
        end
        xlabel('Time (s)'); colormap parula;
end
drawnow;
end

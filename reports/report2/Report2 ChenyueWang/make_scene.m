function [x,target,fs,active] = make_scene(seed,pan,rho)
% MAKE_SCENE Original synthetic music with controlled stereo background.
% pan is the right/left target amplitude ratio. rho is background correlation.
fs = 16000; t = (0:6*fs-1)'/fs; s = zeros(size(t));
notes = [330 440 392 523 440 659];
for j = 1:numel(notes)
    u = t-(0.5+(j-1)*0.8); on = u>=0 & u<0.65;
    v = u(on); env = sin(pi*v/0.65).^2;
    s(on) = env.*(sin(2*pi*notes(j)*v) + ...
        0.35*sin(4*pi*notes(j)*v)+0.15*sin(6*pi*notes(j)*v));
end
active = t>=0.5 & t<5.3; % Includes pauses; fixed for every method.
g = [1 pan]/sqrt(1+pan^2); target = s*g;
rng(seed,'twister'); z = randn(numel(t),3);
% Same coloured spectrum in each channel; no external data are required.
z = filter(1,[1 -0.75],z); z = z-mean(z,1);
z = z./sqrt(mean(z.^2,1));
noise = sqrt(1-rho)*z(:,1:2)+sqrt(rho)*z(:,3);
% Calibrate exact aggregate stereo input SNR to 0 dB in the scored region.
noise = noise*sqrt(sum(target(active,:).^2,'all')/...
    sum(noise(active,:).^2,'all'));
x = target+noise;
% ONE common scale preserves input SNR and all interchannel level cues.
scale = 0.8/max(abs(x),[],'all'); x=x*scale; target=target*scale;
end

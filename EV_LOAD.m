arrival_orig=zeros(20,10000);
arrival_waitng=zeros(20,10000);
charge_time=zeros(20,10000);
occupancyx=zeros(500,10000);



lbd=[2250;3500;3750;5000;5000;3300;2500;1000;200;120;90;65;60;50;40;35;30;27;30;35;45;60;90;120];
%1/lambda per hour These numbers have been rounded to anonimize the
%specifics of our confidential dataset. They provide a close approximation
%but not the exact numbers

avrcg=[120;120;120;120;120;120;120;120;20;20;20;20;20;20;20;20;20;20;20;20;30;30;30;30];
%average charging time per hour

ups=[180;120;120;120;120;120;120;120;60;60;60;60;60;60;60;60;60;60;60;60;60;60;60;60];
%max charging duration per hour

sigma=[10;10;10;10;10;10;10;10;5;5;5;5;5;5;5;5;5;5;5;5;5;5;5;5];
%standard deviation of charging duration per hour

EVCSnb=133184;
%number of EVCSs in your grid or on a specific bus

for j=1:1:EVCSnb
j;
b=j;

arrTime1 = [];
r = [];
for hr=1:1:24
t1 = 0;
T1 = 60;
lambda1 = 1/lbd(hr,1);
arrTime2 = [];
N1=T1;
event1=zeros(N1,1);
while true 
  t1 = t1 - log(rand)/lambda1;
  if t1 <= T1
    arrTime2(end+1,1) = ceil(t1); 
    arrTime1(end+1,1) = ((hr-1)*60)+ceil(t1); 
    event1(ceil(t1))=1;
else
    break
  end
end



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
z=avrcg(hr,1);
up=ups(hr,1);
sima=sigma(hr,1);

pd = makedist('Normal','mu',z,'sigma',sima);
t = truncate(pd,5,up);
r2 = round(random(t,size(arrTime2,1),1));
%histogram(r,size(arrTime1,1))
%sum(r)/size(arrTime1,1)
r=[r; r2];

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
end


inter_times1=diff(arrTime1);

arrTime1_modif=arrTime1;
inter_times1_modif=inter_times1;

for i=2:1:size(arrTime1,1)

if arrTime1_modif(i)<arrTime1_modif(i-1)+r(i-1)+1
arrTime1_modif(i)=arrTime1_modif(i-1)+r(i-1)+1;

end
end

event1end=arrTime1_modif+r;
ocup1=zeros(size(event1,1),1);
for i=1:1:size(arrTime1_modif,1)

ocup1(arrTime1_modif(i,1):event1end(i,1))=1;

end

a=b
arrival_orig(1:size(arrTime1,1),a)=arrTime1;
arrival_waitng(1:size(arrTime1_modif,1),a)=arrTime1_modif;
charge_time(1:size(r,1),a)=r;
occupancyx(1:size(ocup1,1),a)=ocup1;

end

loadx=sum(occupancyx(1:1440,:)')
loady=loadx';

 %v = nonzeros(charge_time);
 %histogram(v,size(v,1))
 loadz=[];
loadz=(sum(occupancyx(1441:size(occupancyx,1),:)'))';

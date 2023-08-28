ncam = length(params_individual);
outdata = struct();
outdata.IntrinsicMatrix_cv_list = zeros(ncam, 3,3);
outdata.distort_cv_list = zeros(ncam, 5);
for i = 1:length(params_individual)
    param = params_individual{i};
    IntrinsicMatrix_cv = int64(round(param.IntrinsicMatrix' - [0,0,1;0,0,1;0,0,0]));
    IntrinsicMatrix_cv(1,2)=0;
    IntrinsicMatrix_cv(2,1)=0;
    outdata.IntrinsicMatrix_cv_list(i,:,:) = IntrinsicMatrix_cv;
    distort = [param.RadialDistortion(1:2), 0, 0, param.RadialDistortion(3)];
    outdata.distort_cv_list(i,:) = distort;
end

save('intrinsic_cv.mat', '-struct', 'outdata');

img_root_path = "/home/chchien/BrownU/research/Image-Capture-With-RealSense/2024_12_23_23_01_10/";
left_img_folder = "images_left/*.jpg";
right_img_folder = "images_right/*.jpg";
imgs_left = dir(fullfile(img_root_path, left_img_folder));
imgs_right = dir(fullfile(img_root_path, right_img_folder));
index = 11;

img_L = imread(fullfile(imgs_left(index).folder, imgs_left(index).name));
img_R = imread(fullfile(imgs_right(index).folder, imgs_right(index).name));

K_left = [642.702, 0, 642.189; 0, 644.445, 410.259; 0, 0, 1];
K_right = [642.357, 0, 639.048; 0, 644.011, 409.868; 0, 0, 1];
radialDistortion_left = [0.00066852, 0.0197];
tangentialDistortion_left = [0, 0]';
radialDistortion_right = [0.0126, -0.0043];
tangentialDistortion_right = [0, 0]';
imageSize = [size(img_L, 1), size(img_L, 2)];
cameraParams_left = cameraParameters("K", K_left, ...
                                     "RadialDistortion", radialDistortion_left, ...
                                     "TangentialDistortion", tangentialDistortion_left, ...
                                     "ImageSize", imageSize);
cameraParams_right = cameraParameters("K", K_right, ...
                                      "RadialDistortion", radialDistortion_right, ...
                                      "TangentialDistortion", tangentialDistortion_right, ...
                                      "ImageSize", imageSize);
img_L = undistortImage(img_L, cameraParams_left);
img_R = undistortImage(img_R, cameraParams_right);

Rel_R = [0.999989397309312,  -0.000310287554897,   0.004594452153621;
   0.000307103196590,   0.999999712180526,   0.000693776975826;
  -0.004594666101610,  -0.000692358648980,   0.999989204783190];
Rel_T = [-94.418236633125801; -0.134712411266931; 0.280409786672127];
invK_L = inv(K_left);
invK_R = inv(K_right);
skew_T = @(T)[0, -T(3,1), T(2,1); T(3,1), 0, -T(1,1); -T(2,1), T(1,1), 0];

picked_point = [480; 360];
gamma1 = [picked_point; 1];
FundMatrix = invK_R' * (skew_T(Rel_T)*Rel_R) * invK_R;
figure(1);
imshow(img_L); hold on;
plot(gamma1(1), gamma1(2), 'cs', 'LineWidth', 2);
hold off;
pause(0.5);

figure(2);
imshow(img_R); hold on;
%> Compute epipolar line coefficients in pixels
a = FundMatrix(1,:) * gamma1;
b = FundMatrix(2,:) * gamma1;
c = FundMatrix(3,:) * gamma1;

yMin = -c./b;
yMax = (-c - a*size(img_L,2)) ./ b;
line([1, size(img_L,2)], [yMin, yMax], 'Color', 'c', 'LineWidth', 2);


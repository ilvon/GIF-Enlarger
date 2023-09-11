#include <iostream>
#include <cstdio>
#include <filesystem>
#include <vector>
#include <regex>
#include <chrono>
#include <curl/curl.h>
#include <windows.h>
#include <Magick++.h>
#include "argparse.hpp"

// https://imagemagick.org/Magick++/Documentation.html

using namespace std;
namespace fs = filesystem;
using namespace Magick;
ArgumentParser parser("GIF Enlarger");

fs::path __current_exe_path;
int max_dim, max_enl, filter_ind;
vector<fs::path> src_img_list;
MagickCore::FilterType resampler[6] = {
    MagickCore::FilterType::PointFilter, MagickCore::FilterType::BoxFilter,
    MagickCore::FilterType::TriangleFilter, MagickCore::FilterType::HammingFilter,
    MagickCore::FilterType::CubicFilter, MagickCore::FilterType::LanczosFilter};

void args_defining(int ac, char** av){
    parser.add_argument("-d", "--dimension", false, "512", false, 
    "Dimension of the output apng (Default=512px)");
    parser.add_argument("-l", "--limit", false, "12", false, 
    "Limit of the maximum magnification (Default=12, No limit=0)");
    parser.add_argument("-n", "--online", false, "false", true, 
    "Use online image as source");
    parser.add_argument("-i", "--input", false, "gif", false, 
    "Input images format (Default = gif)");
    parser.add_argument("-o", "--output", false, "png", false, 
    "Output images format (Default = png)");
    parser.add_argument("-r", "--resample", false, "0", false, 
    "Set the type of image interpolation (Default = NEAREST)");
    parser.parse_args(ac, av);
    try{
        max_dim = stoi(parser.args["dimension"]);
        max_enl = stoi(parser.args["limit"]);
        filter_ind = stoi(parser.args["resample"]);
    }catch(...){
        cerr << "Please input values with correct data type after flags." << endl;
        exit(1);
    }
}

void get_exe_dir_path(fs::path& __current_path){
    try{
        wchar_t buffer[MAX_PATH];
        GetModuleFileNameW(NULL, buffer, MAX_PATH);
        fs::path exepath = buffer;
        exepath = exepath.u8string();
        __current_path = exepath.parent_path();
    }catch(const exception& err){
        cerr << err.what() << endl;
        exit(1);
    }
}

void get_online_srcimg(vector<fs::path>& dl_list){
    string rawdat;
    cout << "URLs: ";
    getline(cin, rawdat);

    regex urlregex(R"(https?:\/\/[^\s"><]*)");
    sregex_iterator iurl = sregex_iterator(rawdat.begin(), rawdat.end(), urlregex);
    sregex_iterator furl = sregex_iterator();
    string surl;
    
    for(sregex_iterator i = iurl; i != furl; ++i){
        surl = (*i).str();
        const char* filename = surl.substr(surl.find_last_of("/") + 1).c_str();
        string dlname = __current_exe_path.string() + "\\" + filename;
        dl_list.emplace_back(dlname);

        CURL *image;
        CURLcode imgresult;
        FILE *fp = nullptr;
        image = curl_easy_init();
        if (image)
        {
            fp = fopen(filename, "wb");
            if (fp == NULL){
                cerr << "File cannot be opened" << endl;
                exit(1);
            }
            curl_easy_setopt(image, CURLOPT_FOLLOWLOCATION, 1);
            curl_easy_setopt(image, CURLOPT_WRITEFUNCTION, NULL);
            curl_easy_setopt(image, CURLOPT_WRITEDATA, fp);
            curl_easy_setopt(image, CURLOPT_URL, surl.c_str());
            curl_easy_setopt(image, CURLOPT_USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36");
            imgresult = curl_easy_perform(image);
            if (imgresult){
                cerr << "Cannot grab the image!" << endl;
                exit(1);
            }
        }
        curl_easy_cleanup(image);
        fclose(fp);
    }
}

// source images from the same directory of the exe
// src_img_list: relative path name
void get_img_list(string format, fs::path p_src){
    fs::path name;
    try{
        for(const auto& result : fs::directory_iterator(p_src)){
            if(fs::is_regular_file(result.path())){
                name = result.path().filename();
                if(format == name.extension().string()){
                    src_img_list.push_back(name);
                }
            }
        }
    }catch(const fs::filesystem_error& ex){
        cerr << "Error: " << ex.what() << endl;
        exit(1);
    }
}

// source images from different directroy (add by drag n drop)
// src_img_list: absolute path
void get_img_list(int argc, char** argv){
    fs::path name;
    try{
        for(int j = 1; j < argc; j++){
            string pathstr = argv[j];
            name = pathstr;
            src_img_list.push_back(name);
        }
    }catch(const exception& err){
        cerr << "Error: " << err.what() << endl;
        exit(1);
    }
}

Geometry img_resize_cal(string name, int max_size, int max_multiple){
    Image srcimg;
    srcimg.ping(name + "[0]");
    size_t w = srcimg.size().width();
    size_t h = srcimg.size().height();
    size_t _side_max = w > h ? w : h;
    int mult_result = max_size / _side_max;
    if(max_multiple == 0){
        return Geometry(w*mult_result, h*mult_result);
    }
    return mult_result > max_multiple ? Geometry(w*max_multiple, h*max_multiple) : Geometry(w*mult_result, h*mult_result);
}

string mkdir_out(fs::path dir_name, fs::path img_name){
    fs::path new_dir;
    if(parser.__is_infile){
        new_dir = img_name.parent_path() / dir_name;
        img_name = img_name.filename();
    }else{
        new_dir = __current_exe_path / dir_name;
    }
    try{
        if(!fs::exists(new_dir) || !fs::is_directory(new_dir)){
            fs::create_directory(new_dir);
        }
    }catch(const fs::filesystem_error& err){
        cerr << err.what() << endl;
        exit(1);
    }
    string new_img_str = (new_dir/img_name).string();
    return new_img_str.substr(0, new_img_str.find_last_of(".") + 1) + parser.args["output"];
}

void disasm_asm_wrt(fs::path ori_img){
    string target_images_str;
    const string _out_dir = "enlarged";
    vector<Image> fm_list, coalesce_fm, export_fm; 
    try{
        string sori_img = ori_img.string();
        target_images_str = mkdir_out(_out_dir, ori_img);
        size_t ping_ind = 0;
        Geometry canvas_size = Geometry(max_dim, max_dim);
        Geometry cont_size = img_resize_cal(sori_img, max_dim, max_enl);
        MagickCore::GravityType f_mg = MagickCore::GravityType::CenterGravity; 
        Color trans("rgba(255,255,255,0)"); //CSS color string

        readImages(&fm_list, sori_img);
        coalesceImages(&coalesce_fm, fm_list.begin(), fm_list.end());
        for(auto& fm : coalesce_fm){
            fm.filterType(resampler[filter_ind]);
            fm.resize(cont_size);
            Image bkgnd(canvas_size, trans);
            bkgnd.composite(fm, f_mg, MagickCore::CompositeOperator::OverCompositeOp);
            bkgnd.gifDisposeMethod(MagickCore::DisposeType::PreviousDispose);
            Image p_img;
            p_img.ping(sori_img + "[" + to_string(ping_ind) + "]");
            bkgnd.animationDelay(p_img.animationDelay());
            export_fm.emplace_back(bkgnd);
            ping_ind++;
        }
        if (parser.args["output"] == "png"){
            writeImages(export_fm.begin(), export_fm.end(), "APNG:"+target_images_str, true);
        }else{
            writeImages(export_fm.begin(), export_fm.end(), target_images_str, true);
        }
        ping_ind = 0;
        fm_list.clear();
        coalesce_fm.clear();
        export_fm.clear();
    }catch(exception& err){
        cerr << err.what() << endl;
        exit(1);
    }
}

void gif_enlarger_main(int argc, char **argv){
    InitializeMagick(*argv);
    vector<fs::path> online_img_list;
    args_defining(argc, argv);
    get_exe_dir_path(__current_exe_path);
    if(parser.args_tog["online"]){
        get_online_srcimg(online_img_list);
    }
    auto __start_time = chrono::steady_clock::now();
    if(parser.__is_infile){
        get_img_list(argc, argv);
    }else{
        get_img_list("." + parser.args["input"], __current_exe_path);
    }
    for(fs::path filename : src_img_list){
        disasm_asm_wrt(filename);
    }
    for(fs::path _reqdel : online_img_list){
        try{
            remove(_reqdel);
        }catch(const fs::filesystem_error& er){
            cerr << er.what() << endl;
            exit(1);
        }
    }
    auto __end_time = chrono::steady_clock::now();
    cout << "\nExecution time: " << 
    chrono::duration_cast<chrono::seconds>(__end_time-__start_time).count() << " seconds" << endl;
    system("pause");
}


int main(int argc, char** argv){
    gif_enlarger_main(argc, argv);
    return 0;
}


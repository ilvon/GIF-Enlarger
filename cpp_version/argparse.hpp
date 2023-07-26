#ifndef ARGUMENTPARSER_H
#define ARGUMENTPARSER_H

#include <iostream>
#include <string>
#include <vector>
#include <map>

class ArgumentParser {
    public:
        std::map<std::string, std::string> args;
        std::map<std::string, bool> args_tog;
        // std::vector<std::string> infiles;
        bool __is_infile = false;
        ArgumentParser(std::string name) : help_title(name){}

        void add_argument(const std::string& flag_abbrv, const std::string& flag_full, bool required, 
        const std::string& default_val="", bool toggle = false, const std::string& description="") 
        {
            std::string metavar = flag_full.substr(2); 
            arguments[metavar] = ArgumentData(flag_abbrv, flag_full, description, required, default_val, toggle);
            arg_v_init(metavar, default_val, toggle);
            if(required){
                req_flag_list.emplace_back(metavar);
            }
        }

        void parse_args(int argc, char** argv) {
            add_argument("-h", "--help", false, "true", true, "Show this help message.");
            bool _is_valid_flag = false;
            for(int i = 1; i < argc; i++){
                std::string p_arg = argv[i];
                if(p_arg == "-h" || p_arg == "--help"){
                    print_usage();
                    exit(0);
                }
                if(i == 1 && p_arg.substr(0,1)!="-" && p_arg.find(":\\") == std::string::npos){
                    std::cerr << "Missing flag!" << std::endl;
                    exit(1);
                }
                if(p_arg.substr(0,1) == "-"){
                    _is_valid_flag = chk_flags(p_arg);
                    if(_is_valid_flag){
                        in_flag_list.emplace_back(found_args);
                        if(arguments[found_args].toggle==true){
                            args_tog[found_args] = !args_tog[found_args];
                        }
                    }else{
                        std::cerr << "Invalid flag!" << std::endl;
                        exit(1);
                    }
                    _is_valid_flag = false;
                }else{
                    if(p_arg.find(":\\") == std::string::npos){
                        args[found_args] = p_arg;
                    }else{
                        // infiles.emplace_back(p_arg); <- parse args (file path)
                        __is_infile = true;
                        return;
                    }
                }
            }
            if(!chk_req(in_flag_list, req_flag_list)){
                std::cerr << "Insufficient flags!" << std::endl;
                exit(1);
            }
        }

        void print_usage() {
            std::cout << "Usage: ./" << help_title << " [-h]";
            for (const auto& argument : arguments) {
                if(argument.first != "help"){
                    const std::string& name = argument.second.flags[0];
                    const std::string& description = argument.second.description;
                    std::cout << " [" << name << "]";
                }
            }
            std::cout << "\n\nOptions:" << std::endl;
            std::cout << "-h, --help" << std::endl;
            std::cout.width(75);
            std::cout<< arguments["help"].description << std::endl;
            for (const auto& argument : arguments) {
                if(argument.first != "help"){
                    const std::string& name = argument.second.flags[0] + ", " + argument.second.flags[1] ;
                    std::cout << name << std::endl << std::endl;
                    std::cout.width(75);
                    std::cout<< argument.second.description << std::endl; 
                }
            }
        }
        
    private:
        std::string help_title;
        std::string found_args;
        struct ArgumentData {
            std::string description;
            bool required;
            std::string default_vals;
            std::vector<std::string> flags;
            bool toggle;
            ArgumentData() : required(false) {}
            ArgumentData(const std::string& s_flag, const std::string& f_flag, const std::string& desc, bool req, const std::string& defv, bool tog) {
                flags.emplace_back(s_flag);
                flags.emplace_back(f_flag);
                description = desc;
                required = req;
                default_vals = defv;
                toggle = tog;
            }
        };
        
        std::map<std::string, ArgumentData> arguments;
        std::vector<std::string> req_flag_list;
        std::vector<std::string> in_flag_list;

        bool chk_flags(const std::string& opt){
            for(const auto& argument : arguments){
                for(const std::string fname : argument.second.flags){
                    if(opt == fname){
                        found_args = argument.first;
                        return true;
                    }
                }
                // const std::vector<std::string>& flag_vec = argument.second.flags;
                // if(find(flag_vec.begin(), flag_vec.end(), opt) != flag_vec.end()){ //#include <algorithm>
                //     found_args = argument.first;
                //     return true;
                // }
            }
            return false;
        }

        void arg_v_init(std::string full_key, std::string defv, bool tog){
            if(tog){
                args_tog[full_key] = (defv=="true") ? true : false;
            }else{
                args[full_key] = defv;
            }
        }

        bool chk_req(std::vector<std::string> in_f, std::vector<std::string> req_f){
            bool is_subset = true;
            bool is_reqf_exist = false;
            for(int i = 0; i < req_f.size(); i++){
                is_reqf_exist = false;
                for(int j = 0; j < in_f.size(); j++){
                    if(req_f[i] == in_f[j]){
                        is_reqf_exist = true;
                        break;
                    }
                }
                if(!is_reqf_exist){
                    is_subset = false;
                    break;
                }
            }
            return is_subset;
        }
};
#endif

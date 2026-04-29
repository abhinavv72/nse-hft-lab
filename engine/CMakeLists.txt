cmake_minimum_required(VERSION 3.20)
project(nse_hft_lab_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(matching_engine_lib
  cpp/matching_engine.cpp
)
target_include_directories(matching_engine_lib PUBLIC cpp)

add_executable(nse_matching_engine cpp/bindings.cpp)
target_link_libraries(nse_matching_engine PRIVATE matching_engine_lib)

add_executable(test_matching_engine tests/test_matching_engine.cpp)
target_link_libraries(test_matching_engine PRIVATE matching_engine_lib)

cmake_minimum_required(VERSION 3.10)
project(robot-common VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Library
add_library(robot-common
    src/ConstantPool.cpp
    src/OpcodeRegistry.cpp
    src/ProgramPrinter.cpp
)

target_include_directories(robot-common PUBLIC include)

# Unit tests (using Catch2)
find_package(Catch2 QUIET)
if(NOT Catch2_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG        v3.5.2
    )
    FetchContent_MakeAvailable(Catch2)
endif()

enable_testing()

add_executable(robot-common-tests
    tests/test_main.cpp
    tests/test_opcode.cpp
    tests/test_operand.cpp
    tests/test_instruction.cpp
    tests/test_function.cpp
    tests/test_program.cpp
    tests/test_constant_pool.cpp
    tests/test_registry.cpp
    tests/test_printer.cpp
)

target_link_libraries(robot-common-tests PRIVATE robot-common Catch2::Catch2WithMain)

add_test(NAME robot-common-tests COMMAND robot-common-tests)
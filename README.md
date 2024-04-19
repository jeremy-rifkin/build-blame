# build-blame

Build-blame is tool to help answer the question: Why are my builds taking so long??

Note: This is very much a work-in-progress. The ease of use is nowhere near what I would consider acceptable for a
finished project.

Currently it requires a project using ninja and clang and a compile_commands.json file.

Preview:

![](screenshots/preview.png)
![](screenshots/full-trace.png)
![](screenshots/includes.svg)




## How to use:

In your project
```
cmake -B build -S . -DCMAKE_CXX_COMPILER=clang++-17 -DCMAKE_C_COMPILER=clang-17 -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=On -GNinja -DCMAKE_CXX_FLAGS=-ftime-trace -DCMAKE_C_FLAGS=-ftime-trace
```

Then
```
python3 main.py --project-folder /path/to/project --output out
```


## Example Statistics

Example output, on top of traces and graphs above:

```
Slowest translation unit targets:
      Time  Target
    3.797s  /home/rifkin/projects/libassert/build-clang/_deps/googletest-src/googletest/src/gtest-all.cc
     3.57s  /home/rifkin/projects/libassert/src/analysis.cpp
    3.316s  /home/rifkin/projects/libassert/tests/integration/integration.cpp
    2.795s  /home/rifkin/projects/libassert/build-clang/_deps/cpptrace-src/src/symbols/symbols_with_libdwarf.cpp
    2.713s  /home/rifkin/projects/libassert/tests/demo/demo.cpp
    2.661s  /home/rifkin/projects/libassert/build-clang/_deps/googletest-src/googlemock/src/gmock-all.cc
    2.604s  /home/rifkin/projects/libassert/tests/unit/lexer.cpp
    2.407s  /home/rifkin/projects/libassert/tests/unit/literals.cpp
    2.349s  /home/rifkin/projects/libassert/build-clang/_deps/zstd-src/lib/compress/zstd_lazy.c
    2.331s  /home/rifkin/projects/libassert/tests/unit/fmt-test.cpp
    2.246s  /home/rifkin/projects/libassert/tests/unit/stringify.cpp
    2.006s  /home/rifkin/projects/libassert/src/assert.cpp
    1.819s  /home/rifkin/projects/libassert/tests/binaries/catch2-demo.cpp
    1.802s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/catch_session.cpp
     1.77s  /home/rifkin/projects/libassert/tests/binaries/gtest-demo.cpp
    1.711s  /home/rifkin/projects/libassert/build-clang/_deps/googletest-src/googlemock/src/gmock_main.cc
    1.705s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/internal/catch_commandline.cpp
    1.646s  /home/rifkin/projects/libassert/src/paths.cpp
     1.64s  /home/rifkin/projects/libassert/build-clang/_deps/cpptrace-src/src/cpptrace.cpp
    1.608s  /home/rifkin/projects/libassert/src/utils.cpp
 1m 54.85s  Other

Slowest link targets:
    Time  Target
 10.712s  fmt-test
 10.528s  lexer
 10.449s  catch2-demo
 10.384s  gtest-demo
 10.189s  integration
 10.003s  stringify
  9.991s  demo
  9.204s  type_handling
  9.198s  test_public_utilities
  9.147s  basic_test
  9.064s  disambiguation
  8.994s  test_type_prettier
  8.985s  tokens_and_highlighting
  2.299s  literals
  1.665s  _deps/catch2-build/src/libCatch2d.a
   808ms  _deps/zstd-build/lib/libzstd.a
   609ms  _deps/cpptrace-build/libcpptrace.a
   443ms  _deps/libdwarf-build/src/lib/libdwarf/libdwarf.a
   371ms  libassert.a
   297ms  lib/libgtest.a
   612ms  Other

Frontend/Backend:
      Time  Target
 1m 55.08s  Frontend
   17.986s  Backend

Includes:
         Time  Target
   350m 5.29s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/string
  257m 34.60s  /home/rifkin/projects/libassert/include/libassert/assert.hpp
  238m 22.07s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/ios
  214m 46.24s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/ostream
  168m 20.68s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/ios_base.h
  164m 45.54s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/basic_string.h
  158m 43.60s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/internal/catch_stringref.hpp
   118m 2.46s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/locale_classes.h
  106m 26.69s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/internal/catch_reusable_string_stream.hpp
  103m 36.87s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/interfaces/catch_interfaces_reporter.hpp
  102m 31.32s  /home/rifkin/projects/libassert/build-clang/_deps/googletest-src/googletest/include/gtest/gtest.h
    90m 6.77s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/memory
   82m 30.24s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/catch_tostring.hpp
    79m 0.74s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/internal/catch_assertion_handler.hpp
   78m 33.74s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/reporters/catch_reporter_common_base.hpp
   72m 54.26s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/vector
   66m 39.92s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/matchers/internal/catch_matchers_impl.hpp
   64m 41.41s  /home/rifkin/projects/libassert/build-clang/_deps/cpptrace-src/include/cpptrace/cpptrace.hpp
   62m 55.62s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/locale_facets.h
    61m 4.86s  /home/rifkin/projects/libassert/build-clang/_deps/catch2-src/src/catch2/../catch2/matchers/catch_matchers.hpp
 4356m 26.35s  Other

Includes excluding children:
        Time  Target
  72m 15.39s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/basic_string.h
  36m 18.53s  /home/rifkin/projects/libassert/include/libassert/assert.hpp
  34m 15.73s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/locale_facets.tcc
  33m 20.19s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/type_traits
  32m 21.96s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/chrono.h
  31m 34.56s  /usr/include/features.h
  31m 32.07s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/tuple
  22m 57.07s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_bvector.h
  20m 57.42s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_function.h
  20m 20.92s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algobase.h
  19m 26.89s  /usr/include/stdlib.h
   19m 9.41s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/string_view
  18m 36.78s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/limits
  16m 37.90s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/locale_facets.h
  15m 57.00s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/ios_base.h
  15m 55.51s  /home/rifkin/projects/libassert/build-clang/_deps/magic_enum-src/include/magic_enum/magic_enum.hpp
  13m 58.93s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/system_error
  13m 25.59s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_tree.h
  13m 20.27s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unordered_map.h
  13m 15.04s  /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/ext/string_conversions.h
 964m 13.43s  Other

Instantiations:
         Time  Target
   13m 40.01s  std::basic_regex<char>::_M_compile
    13m 2.33s  std::__detail::_Compiler<std::regex_traits<char>>::_Compiler
   11m 45.17s  std::vformat_to<std::__format::_Sink_iter<char>>
   11m 44.17s  std::__format::__do_vformat_to<std::__format::_Sink_iter<char>, char, std::basic_format_context<std::__format::_Sink_iter<char>, char>>
   11m 27.17s  test_class<int>::something<N>
   11m 27.15s  test_class<int>::something_else
   11m 13.34s  std::__detail::_Compiler<std::regex_traits<char>>::_M_disjunction
    11m 9.24s  std::__detail::_Compiler<std::regex_traits<char>>::_M_alternative
   10m 59.62s  std::__detail::_Compiler<std::regex_traits<char>>::_M_term
    10m 8.47s  std::vformat_to<std::__format::_Sink_iter<wchar_t>>
    10m 7.18s  std::__format::__do_vformat_to<std::__format::_Sink_iter<wchar_t>, wchar_t, std::basic_format_context<std::__format::_Sink_iter<wchar_t>, wchar_t>>
    9m 31.99s  std::__format::_Formatting_scanner<std::__format::_Sink_iter<char>, char>::_Formatting_scanner
    9m 18.59s  std::__detail::_Compiler<std::regex_traits<char>>::_M_atom
    8m 33.17s  std::__format::_Formatting_scanner<std::__format::_Sink_iter<char>, char>::_M_format_arg
    8m 11.38s  std::__format::_Formatting_scanner<std::__format::_Sink_iter<wchar_t>, wchar_t>::_Formatting_scanner
    7m 55.85s  std::basic_regex<char>::basic_regex<std::char_traits<char>, std::allocator<char>>
     7m 1.40s  std::__format::_Formatting_scanner<std::__format::_Sink_iter<wchar_t>, wchar_t>::_M_format_arg
     6m 6.39s  __gnu_cxx::__to_xstring<std::basic_string<wchar_t>, wchar_t>
    5m 57.66s  std::basic_string<char16_t>
    5m 45.02s  std::basic_regex<char>::basic_regex
 1065m 57.95s  Other

Instantiations excluding children:
        Time  Target
   5m 47.51s  std::basic_string<char16_t>
   5m 23.19s  std::basic_string<char>
   5m 18.56s  std::basic_string<wchar_t>
   5m 18.18s  std::basic_string<char32_t>
    3m 6.63s  std::basic_string<char32_t>::_M_construct<const char32_t *>
   2m 59.29s  std::basic_string<char16_t>::_M_construct<const char16_t *>
   2m 25.09s  std::basic_string<wchar_t>::_M_construct<wchar_t *>
   1m 48.13s  std::operator+<char, std::char_traits<char>, std::allocator<char>>
   1m 47.50s  std::_Hashtable<int, std::pair<const int, int>, std::allocator<std::pair<const int, int>>, std::__detail::_Select1st, std::equal_to<int>, std::hash<int>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, false, true>>
   1m 27.60s  std::basic_string<char>::_M_construct<char *>
   1m 25.82s  __gnu_cxx::__to_xstring<std::basic_string<wchar_t>, wchar_t>
   1m 23.73s  std::__str_concat<std::basic_string<char>>
   1m 20.42s  std::chrono::operator<<long, std::ratio<1, 1000000000>, long, std::ratio<1, 1000000000>>
   1m 20.11s  std::chrono::duration<long, std::ratio<1, 1000000000>>
   1m 18.41s  std::optional<std::basic_string<char>>
   1m 15.90s  std::_Hashtable<int, std::pair<const int, int>, std::allocator<std::pair<const int, int>>, std::__detail::_Select1st, std::equal_to<int>, std::hash<int>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, false, false>>
   1m 11.54s  __gnu_cxx::__to_xstring<std::basic_string<char>, char>
    1m 6.88s  std::reverse_iterator<std::_Bit_iterator>
    1m 6.60s  test_class<int>::something_else
    1m 4.88s  std::basic_string<wchar_t>::basic_string<wchar_t *, void>
 282m 26.49s  Other

Templates resulting in the most instantiations:
        Time  Target
  22m 38.78s  std::__and_
  22m 31.09s  std::basic_string
  21m 53.64s  std::vformat_to
  21m 51.35s  std::__format::__do_vformat_to
  19m 51.30s  std::basic_string::basic_string
  18m 25.89s  std::unique_ptr
  17m 55.99s  magic_enum::detail::values
  17m 46.50s  magic_enum::detail::valid_count
  17m 43.37s  std::__format::_Formatting_scanner::_Formatting_scanner
  17m 15.00s  std::vector
  16m 22.41s  libassert::detail::process_assert_fail
   16m 7.28s  libassert::detail::generate_stringification
  15m 39.62s  testing::internal::MatcherBase::MatcherBase
  15m 34.57s  std::__format::_Formatting_scanner::_M_format_arg
  15m 33.68s  std::__uniq_ptr_data
  15m 33.42s  testing::internal::MatcherBase::Init
  15m 23.25s  std::__uniq_ptr_impl
  15m 15.15s  std::basic_string::_M_construct
  14m 21.00s  std::_Destroy
  13m 43.79s  libassert::detail::process_assert_fail_n
 909m 36.18s  Other

Templates resulting in the most instantiations excluding children:
        Time  Target
   22m 4.42s  std::basic_string
  14m 36.89s  std::__and_
  10m 51.96s  std::basic_string::_M_construct
    8m 3.27s  std::vector
   7m 21.64s  std::_Vector_base
    7m 3.55s  std::__or_
   6m 50.65s  std::chrono::duration
   6m 25.01s  std::pair
   6m 15.15s  magic_enum::detail::is_valid
   5m 35.53s  std::tuple
   5m 12.00s  std::basic_string::basic_string
   4m 18.35s  std::_Hashtable
    4m 3.10s  __gnu_cxx::__stoa
   3m 59.38s  std::__format::__formatter_fp::format
   3m 56.18s  std::vector::_M_realloc_insert
   3m 43.30s  std::is_destructible
   3m 22.80s  std::_Tuple_impl
   3m 15.22s  std::__format::__formatter_int::format
    3m 2.12s  std::__uniq_ptr_impl
   2m 59.12s  std::optional
 197m 22.80s  Other
```

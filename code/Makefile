CXXFLAGS = -std=c++11 -O0 -g -Wall -Wextra -pedantic

default:
	g++ $(CXXFLAGS) -c *.cpp
	ar rcs libdnest4.a *.o
	rm -f *.o
	make nolib -C Examples/SpikeSlab

noexample:
	g++ $(CXXFLAGS) -c *.cpp
	ar rcs libdnest4.a *.o
	rm -f *.o

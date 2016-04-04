#ifndef DNest4_Builder_MyModel
#define DNest4_Builder_MyModel

#include "DNest4/code/DNest4.h"
#include <ostream>
#include <vector>

class MyModel
{
    private:
        double m;
        double b;
        double sigma;

        static const double N;

        static const std::vector<double> x;
        static const std::vector<double> y;



    public:
        // Constructor only gives size of params
        MyModel();

        // Generate the point from the prior
        void from_prior(DNest4::RNG& rng);

        // Metropolis-Hastings proposals
        double perturb(DNest4::RNG& rng);

        // Likelihood function
        double log_likelihood() const;

        // Print to stream
        void print(std::ostream& out) const;

        // Return string with column information
        std::string description() const;
};

#endif


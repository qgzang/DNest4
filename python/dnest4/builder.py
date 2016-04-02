from collections import OrderedDict
from enum import Enum

class Uniform:
    """
    Uniform distributions.
    """
    def __init__(self, a, b):
        self.a, self.b = a, b

    def from_prior(self):
        s = "{x} = {a} + ({b} - ({a}))*rng.rand();\n"
        return self.insert_parameters(s)

    def perturb(self):
        s  = "{x} += ({b} - ({a}))*rng.randh();\n"
        s += "wrap({x}, {a}, {b});\n"
        return self.insert_parameters(s)

    def log_density(self):
        s  = "if({x} < ({a}) || {x} > ({b}))\n"
        s += "    logp = -numeric_limits<double>::max();\n"
        s += "logp += -log({b} - ({a}));\n"
        return self.insert_parameters(s)

    def insert_parameters(self, s):
        s = s.replace("{a}", str(self.a))
        s = s.replace("{b}", str(self.b))
        return s

class Normal:
    """
    Normal distributions.
    """
    def __init__(self, mu, sigma):
        self.mu, self.sigma = mu, sigma

    def from_prior(self):
        s = "{x} = {mu} + {sigma}*rng.randn();\n"
        return self.insert_parameters(s)

    def perturb(self):
        s  = "log_H -= -0.5*pow(({x}) - ({mu}))/({sigma}), 2);\n"
        s += "{x} += ({sigma})*rng.randh();\n"
        s += "log_H += -0.5*pow((({x}) - ({mu}))/({sigma}), 2);\n"
        return self.insert_parameters(s)

    def log_density(self):
        s  = "logp += -0.5*log(2*M_PI) - log({sigma}) "
        s += "- 0.5*pow((({x}) - ({mu}))/({sigma}), 2);\n"
        return self.insert_parameters(s)

    def insert_parameters(self, s):
        s = s.replace("{mu}", str(self.mu))
        s = s.replace("{sigma}", str(self.sigma))
        return s

class NodeType(Enum):
    """
    To distinguish between different kinds of Nodes
    """
    coordinate = 1
    derived = 2
    data = 3
    prior_info = 4

class Node:
    """
    A single parameter or data value.
    """
    def __init__(self, name, prior=None, index=None,\
                    node_type=NodeType.coordinate):
        self.name = name
        self.prior = prior
        self.node_type = node_type
        self.index = index
        if index is not None:
            self.name += "[" + str(index) + "]"

    def from_prior(self):
        return self.prior.from_prior().replace("{x}", self.name)

    def perturb(self):
        return self.prior.perturb().replace("{x}", self.name)

    def log_density(self):
        return self.prior.log_density().replace("{x}", self.name)

    def __str__(self):
        return self.name

class Model:
    def __init__(self):
        self.nodes = OrderedDict()

    def add_node(self, node):
        self.nodes[node.name] = node

    def from_prior(self):
        """
        Generate the from_prior code for the whole model.
        """
        s = ""
        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == NodeType.coordinate:
                s += node.from_prior()

        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == NodeType.derived:
                s += node.from_prior()
        return s

    def perturb(self):
        """
        Generate perturb code for the whole model.
        """
        # Count the number of coordinates
        num_coords = 0
        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == NodeType.coordinate:
                num_coords += 1

        # Choose which one to perturb
        s =  "double log_H = 0.0;\n"
        s += "int which = rng.rand_int({n});\n".replace("{n}", str(num_coords))

        # The if-statements
        k = 0
        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == NodeType.coordinate:
                s += "if(which == {k})\n{\n".replace("{k}", str(k))
                s += "\n".join(["    " + x for x in node.perturb().splitlines()])
                s += "\n}\n"
                k += 1

        s += "return log_H;\n"
        return s

    def print_code(self):
        """
        Generate print code for the whole model.
        """
        s = ""
        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == NodeType.coordinate:
                s += "out<<" + str(node) + "<<\" \";\n"
        return s

    def description(self):
        """
        Generate description code for the whole model.
        """
        s = "string s;\n"
        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == NodeType.coordinate:
                s += "s += \"" + str(node) + ", \";\n"
        s = s[0:-5]
        s += "\";"
        s += "\nreturn s;"
        return s

    def log_likelihood(self):
        """
        Generate the log_likelihood code for the whole model.
        """
        s = "double logp = 0.0;\n\n"
        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == NodeType.data:
                s += node.log_density()
        s += "\nreturn logp;"
        return s

    def get_vector_names(self, node_type):
        """
        Return a set of names of vectors of a certain NodeType.
        """
        vecs = set()
        for name in self.nodes:
            node = self.nodes[name]
            if node.node_type == node_type and\
               node.index is not None:
                vecs.add(name.split("[")[0])
        return vecs

    def generate_h(self):
        """
        Load MyModel.h.template
        and fill in the required declarations.
        """
        # Prepare the declarations for MyModel.h
        declarations = ""

        # Declare scalar unknowns
        for name in self.nodes:
            node = self.nodes[name]
            if node.index is None and (node.node_type == NodeType.coordinate or\
                                       node.node_type == NodeType.derived):
                declarations += "        "
                declarations += "double {x};\n".replace("{x}", node.name)

        # Declare vector unknowns
        vecs = self.get_vector_names(NodeType.coordinate)
        vecs = vecs.union(self.get_vector_names(NodeType.derived))
        for vec in vecs:
            declarations += "        "
            declarations += "std::vector<double> {x};\n".replace("{x}",\
                             vec)

        declarations += "\n"

        # Declare scalar knowns
        for name in self.nodes:
            node = self.nodes[name]
            if node.index is None and (node.node_type == NodeType.data or\
                                       node.node_type == NodeType.prior_info):
                declarations += "        static const "
                declarations += "double {x};\n".replace("{x}", node.name)
        declarations += "\n"

        # Declare vector knowns
        vecs = self.get_vector_names(NodeType.data)
        vecs = vecs.union(self.get_vector_names(NodeType.prior_info))
        for vec in vecs:
            declarations += "        static const "
            declarations += "std::vector<double> {x};\n".replace("{x}",\
                             vec)

        declarations += "\n"

        # Open the template .h file
        f = open("MyModel.h.template")
        s = f.read()
        s = s.replace("        {DECLARATIONS}", declarations)
        f.close()

        # Write the new .h file
        f = open("MyModel.h", "w")
        f.write(s)
        f.close()

        return s


    def generate_cpp(self):
        """
        Load MyModel.cpp.template
        and fill in the required stuff.
        """
        # Prepare the from_prior code
        from_prior = self.from_prior()
        from_prior = ["    " + x for x in from_prior.splitlines()]
        from_prior = "\n".join(from_prior)

        # Prepare the perturb code
        perturb = self.perturb()
        perturb = ["    " + x for x in perturb.splitlines()]
        perturb = "\n".join(perturb)

        # Prepare the log_likelihood code
        log_likelihood = self.log_likelihood()
        log_likelihood = ["    " + x for x in log_likelihood.splitlines()]
        log_likelihood = "\n".join(log_likelihood)

        # Prepare the print code
        print_code = self.print_code()
        print_code = ["    " + x for x in print_code.splitlines()]
        print_code = "\n".join(print_code)

        # Prepare the description code
        description = self.description()
        description = ["    " + x for x in description.splitlines()]
        description = "\n".join(description)

        # Open the template .cpp file
        f = open("MyModel.cpp.template")
        s = f.read()

        # Do the replacements
        s = s.replace("{FROM_PRIOR}", from_prior)
        s = s.replace("{PERTURB}", perturb)
        s = s.replace("{LOG_LIKELIHOOD}", log_likelihood)
        s = s.replace("{PRINT}", print_code)
        s = s.replace("{DESCRIPTION}", description)
        f.close()

        # Write the new .h file
        f = open("MyModel.cpp", "w")
        f.write(s)
        f.close()

        return s



if __name__ == "__main__":
    # Create a model
    model = Model()

    # Add three parameters to it
    model.add_node(Node("m", Uniform(-10.0, 10.0)))
    model.add_node(Node("b", Uniform(-10.0, 10.0)))
    model.add_node(Node("sigma", Uniform(0.0, 10.0)))

    # Add five data values
    for i in range(0, 5):
        model.add_node(Node("x", 3.2, node_type=NodeType.prior_info, index=i))
        model.add_node(Node("y", Normal("m*x[{i}] + b".format(i=i),\
                                    model.nodes["sigma"]),\
                                    node_type=NodeType.data, index=i))

    model.add_node(Node("C", 5.4, node_type=NodeType.prior_info))

    # Generate the .h file
    model.generate_h()
    model.generate_cpp()


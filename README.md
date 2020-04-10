# PypeFlow 2020.0

*A Python package, written in Python 3.7, for designing and analyzing piping networks using SI-units.*

**Designing** a piping network involves finding a solution for two kinds of problems:

1. The design flow rates in the pipe sections composing the network are known. Also known are the available friction losses due to fluid flow in the pipe sections. The problem remains to find appropriate diameters for the pipe sections, so that the known flow rates do not generate friction losses that exceed the available values.
2. The design flow rates in the pipe sections composing the network are known. Also known are the diameters of the pipe sections and the fittings/valves present in each pipe section of the network. 
The problem consists of finding the pressure drops across the pipe sections when design flow rates are flowing.

Once a piping network is designed, PypeFlow can search for all possible flow paths between the start
and the end node of the network. This allows for flow balancing the different branches in the network. One
can add balancing valves in certain pipe sections to accomplish this. PypeFlow will then calculate the Kvr setting of each balancing valve in the network, so that all flow paths retrieve the same pressure drop when the design flow rates are flowing in the pipe sections. Without flow balancing it is uncertain whether the desired flow rate will flow in each of the pipe sections.

**Analyzing** a piping network involves finding the steady flow rate and pressure distribution in a known piping network. For this, PypeFlow uses the Hardy Cross method. One can also add pumps to the network and make use of so called pseudo sections for networks that are open (e.g. drinking water installations).

Input data for letting PypeFlow design or analyze a piping network comes from a network configuration file.
This is just a csv-file that can be made with any spreadsheet program. The network configuration is entered by the user in a table in which each row represents a pipe section of the network.

PypeFlow is (at this moment) only an API, which means that one should interact with PypeFlow through Python scripts. Jupyter Notebook is also an excellent tool for doing the design and analysis of a piping network using PypeFlow. 

Usage examples can be found within the folders *scripts* (pure Python scripts) and *notebooks* (Jupyter notebooks) of the main *examples* folder.

The PypeFlow API documentation, created with [pdoc3](https://pdoc3.github.io/pdoc/), can be found in the folder *docs/pypeflow*. To access the documentation one can download the repository, unzip it and then open *index.html* in a web browser by double clicking the file.

The source code of the project is available in the folder *source_code*. Besides the main package *pypeflow*, there are a few other custom packages that are used by PypeFlow:

- Package *nummath* contains a series of modules for numerical mathematics, based on the book *Numerical Methods in Engineering with Python 3* by Jaan Kiusalaas. It also contains the modules *graphing* and *graphing2* which are just tiny wrappers around *matplotlib* that are meant to create common diagrams more quickly and more intuitively.
- Package *quantities* is a simple package for working with physical quantities in Python. It takes the burden away from the user in converting the value of a quantity from one measuring unit into another.

The custom package *jupyter_addons* is not used by PypeFlow. It just contains a few wrapper functions for displaying things more nicely in a Jupyter Notebook, using the style sheet *my_styles.css* which must reside in the same folder as the Jupyter notebooks (look in the folder *notebooks* of the *examples* folder).

Fluid properties, like mass density and viscosity, are retrieved using [CoolProp Python Wrapper](http://www.coolprop.org/coolprop/wrappers/Python/index.html).

## Installing PypeFlow

Create a virtual environment for your project and install PypeFlow in this environment with:

```
pip install tc-pypeflow
```

## Using PypeFlow

To use PypeFlow, two modules constitute the main user interface:

- For designing a piping network the main module is `pypeflow.design.design`. This module contains the class `Designer` to perform the design procedure.
- For analyzing a piping network the main module `pypeflow.analysis.analysis`. This module contains the class `Analyzer` to perform the analysis procedure.

As already mentioned, PypeFlow needs a network configuration file (csv-file) for doing the design or analysis of a piping network. A network is comprised of nodes that are interconnected by pipe sections. Each section has a start node and an end node. To identify the nodes and sections in the network the user must assign a unique identifier (id) to them, that can be chosen freely (but must be unique in the whole network). A network also has a start and an end node. In a closed network this is evident, but this is less evident in a open network where fluid can leave the network at multiple exits. However, it may be possible to connect these exits through so called pseudo connections and with a common reference node. An example could be the drinking water installation of a building. It has one entrance point, i.e. the start node of the network, but multiple draw-off points, through which water flows into open atmosphere. This could then be regarded as the common reference node, i.e. the fictitious end node of the network. The pressure difference between this end node (at atmospheric pressure) and the start node of the network is the feed pressure that makes the water flowing through the network. Pypeflow is able to find all possible flow paths between the start and end node of the network and with that is also able to balance the network, which is a requirement in e.g. hydronic heating installations. 

For **designing a network**, the csv network configuration file for sections looks like this:

| section_id | start_node_id | start_node_height | end_node_id | end_node_height | length | nom_diameter | flow_rate | pressure_drop |
| ---------- | ------------- | ----------------- | ----------- | --------------- | ------ | ------------ | --------- | ------------- |
| s12        | n1            | 0                 | n2          | 4.4             | 16.7   |              | 1.696     | 0.067         |


Column:

0. id of the section
1. start node id of the section
2. height of the start node with respect to a chosen reference plane
3. end node id of the section
4. height of the end node with respect to a chosen reference plane
5. length of the section
6. nominal diameter (leave empty if not known)
7. design flow rate through the section
8. pressure drop across section due to friction (leave empty if not known)

Fittings and valves are added to a section using a separate csv configuration file that looks like this:

| section_id | fitting_id | type  | zeta | zeta_inf | zeta_d | ELR  | Kv   |
| ---------- | ---------- | ----- | ---- | -------- | ------ | ---- | ---- |
| s12        | elb1       | elbow |      |          |        | 30   |      |

Column:

0. id of the section to which the fitting/valve belongs

1. id of the fitting

2. type of the fitting (can be chosen arbitrarily, just a description for easy reference)

3. `zeta` resistance coefficient

4. `zeta_inf` resistance coefficient

5. `zeta_d` resistance coefficient

6. `ELR` equivalent length ratio

7. `Kv` flow coefficient (based on flow rate in m<sup>3</sup>/h and pressure in bar)

Several ways exist to determine the pressure drop caused by fluid flow through a fitting or valve. PypeFlow supports four different methods:

- the [K-method](https://neutrium.net/fluid_flow/pressure-loss-from-fittings-excess-head-k-method/) uses a single resistance coefficient `zeta` that is coupled to the velocity pressure in the section in which the fitting or valve is present.

- the [3K method](https://neutrium.net/fluid_flow/pressure-loss-from-fittings-3k-method/) uses a set of three resistance coefficients `zeta`, `zeta_inf` and `zeta_d` to determine the pressure loss more precisely.

- the Crane-K-method which is an adaptation of the K-method (see CRANE, *Flow of Fluids Through Valves, Fittings and Pipe*, Technical Paper No. 410M).

- using a flow coefficient `Kv` instead of a resistance coefficient, which is especially the case for valves.

Based on the values that are filled in in the table PypeFlow chooses the appropriate method to calculate the pressure loss across the fitting or valve.

PypeFlow also contains a number of classes that model a number of fittings and valves for which it is possible to calculate the resistance coefficient based on formulas presented in CRANE, *Flow of Fluids Through Valves, Fittings and Pipe*, Technical Paper No. 410M. Take a look at the module `resistance_coefficient.py` in the sub-package `pypeflow.core`. There is also a small module `flow_coefficient.py` in the same sub-package for converting between flow coefficients or to calculate the corresponding flow coefficient if flow rate through and pressure drop across a piping element are known.

Besides ordinary fittings and valves, a section can also be equipped with a balancing valve and a control valve for modulating flow control. These must be added programmatically through the user interface of class `Designer`. How this is done is demonstrated in one of the examples that can be found in this repository.


For **analyzing a network**, the csv network configuration file looks like this:

| loop_id | section_id | start_node_id | end_node_id | diameter | length | zeta  | a0        | a1         | a2         | dp_fixed | flow_rate |
| ------- | ---------- | ------------- | ----------- | -------- | ------ | ----- | --------- | ---------- | ---------- | -------- | --------- |
| l1      | s12        | n1            | n2          | 40       | 16.7   | 6.646 | 5.85E+005 | -5.87E+007 | -4.60E+010 |          | 1.696     |

Column:

0. id of the loop to which the section belongs
1. id of the section in the network
2. id of the start node of the section
3. id of the end node of the section
4. nominal diameter of the section
5. length of the section
6. sum of the resistance coefficients of fittings/valves in the section
7. pump coefficient `a0` in the equation `dp_pump = a0 + a1 * V + a2 * V ** 2` that describes the pump curve of a given pump in the section (leave this empty if no pump is present in the section)
8. pump coefficient `a1`
9. pump coefficient `a2`
10. fixed pressure difference between start and end node of the section (only in case of pseudo section, leave this empty if the section is not a pseudo section)
11. initial guess for the flow rate through the section (leave this empty in case of a pseudo section)

Besides the section and node ids, there is also a loop id, that must identify to which primary loop in the network the section belongs. A section can belong to two loops at most. Loops that have more than two sections in common are not primary loops and are not allowed. Each loop has the same positive reference rotation sense, usually the clockwise sense is taken. Flow rates are assigned a plus sign if their sense or direction coincides with the reference loop sense, otherwise they get a minus sign. The sign of a fixed pressure difference in a loop is determined by the sense of the flow rate it would cause. When the initial guesses for the flow rates are filled in, they must obey the law of conservation of mass, i.e. the sum of the flow rates arriving at a node must be equal to the sum of flow rates that leave the node.

All information needed to analyze a network is passed to PypeFlow through the csv file.

The results of the design and analysis calculations by PypeFlow can be retrieved as Pandas DataFrame objects that can be easily saved to csv or Excel files (see Pandas documentation).

Finally, PypeFlow offers the possibility to draw the system curve of a flow path, the possibility to determine the coefficients of the pump curve of a given pump using curve fitting, and also to draw this pump curve. This functionality is housed in the sub-package `pypeflow.utils`.

The best way to find out how to use PypeFlow is to have a look at the several examples in the *examples* folder of this repository.


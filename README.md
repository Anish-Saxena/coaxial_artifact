<p align="center">
  <h1 align="center"> Coaxial Artifact </h1>
</p>

# Champsim Compile

ChampSim takes a JSON configuration script. Examine `champsim_config.json` for a fully-specified example. All options described in this file are optional and will be replaced with defaults if not specified. The configuration scrip can also be run without input, in which case an empty file is assumed.
```
$ ./config.sh <configuration file>
$ make
```

## Preparing Traces
0. Install the megatools executable

    ```bash
    cd $PYTHIA_HOME/scripts
    wget https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-linux-x86_64.tar.gz
    tar -xvf megatools-1.11.1.20230212-linux-x86_64.tar.gz 
    ```
> Note: The megatools link might change in the future depending on latest release. Please recheck the link if the download fails.

1. Use the `download_traces.pl` perl script to download necessary ChampSim traces used in our paper.

    ```bash
    mkdir $PYTHIA_HOME/traces/
    cd $PYTHIA_HOME/scripts/
    perl download_traces.pl --csv artifact_traces.csv --dir ../traces/
    ```
> Note: The script should download **233** traces. Please check the final log for any incomplete downloads. The total size of all traces would be **~52 GB**.

2. Once the trace download completes, please verify the checksum as follows. _Please make sure all traces pass the checksum test._

    ```bash
    cd $PYTHIA_HOME/traces
    md5sum -c ../scripts/artifact_traces.md5
    ```

3. If the traces are downloaded in some other path, please change the full path in `experiments/MICRO21_1C.tlist` and `experiments/MICRO21_4C.tlist` accordingly.

### More Traces
1. We are also releasing a new set of ChampSim traces from [PARSEC 2.1](https://parsec.cs.princeton.edu) and [Ligra](https://github.com/jshun/ligra). The trace drop-points are measured using [Intel Pinplay](https://software.intel.com/content/www/us/en/develop/articles/program-recordreplay-toolkit.html) and the traces are captured by the ChampSim PIN tool. The traces can be found in the following links. To download these traces in bulk, please use the "Download as ZIP" option from mega.io web-interface.
      * PARSEC-2.1: https://bit.ly/champsim-parsec2
      * Ligra: https://bit.ly/champsim-ligra


# Run simulation

Execute the binary directly.
```
$ bin/champsim --warmup_instructions 200000000 --simulation_instructions 500000000 ~/path/to/traces/600.perlbench_s-210B.champsimtrace.xz
```

The number of warmup and simulation instructions given will be the number of instructions retired. Note that the statistics printed at the end of the simulation include only the simulation phase.

# How to create traces

Program traces are available in a variety of locations, however, many ChampSim users wish to trace their own programs for research purposes.
Example tracing utilities are provided in the `tracer/` directory.

# Evaluate Simulation

ChampSim measures the IPC (Instruction Per Cycle) value as a performance metric. <br>
There are some other useful metrics printed out at the end of simulation. <br>

Good luck and be a champion! <br>

# DRAMSim3 setup

Follow build instruction from official DRAMSim3 - https://github.com/umd-memsys/DRAMsim3
Update the path to DRAMSim library and the ini files in config.py

# Processing the runs and plotting

Processing and plotting scripts can be found in SCRIPTS. 
## Build order and instructions to run scripts in SCRIPTS.
## lines that need modification (PATH specification) are marked by SCAE in all files throuhgout the process 

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
0. Install the megatools executable. Megatools.tar.gz is already included, but you can get it with wget if broken

    ```bash
    wget https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-linux-x86_64.tar.gz
    tar -xvf megatools-1.11.1.20230212-linux-x86_64.tar.gz 
    ```
> Note: The megatools link might change in the future depending on latest release. Please recheck the link if the download fails.

1. Use the `download_traces.pl` perl script to download necessary ChampSim traces used in our paper. (Update megtool path in the .pl file)

    ```bash
    perl (PATH_TO)download_traces.pl --csv (PATH_TO)artifact_traces.csv --dir PATH_TO_DIR
    ```
> Note: The script should download **233** traces. Please check the final log for any incomplete downloads. The total size of all traces would be **~52 GB**.
> If AE committee just needs to see a quantitative reproduction, not all 233 traces are needed. 



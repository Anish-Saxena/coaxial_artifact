/*
 *    Copyright 2023 The ChampSim Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*! @file
 *  This is an example of the PIN tool that demonstrates some basic PIN APIs 
 *  and could serve as the starting point for developing your first PIN tool
 */

#include "pin.H"
#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <string.h>
#include <string>

#include "../../inc/trace_instruction.h"

using trace_instr_format_t = input_instr;

/* ================================================================== */
// Global variables 
/* ================================================================== */

//UINT64 instrCount = 0;
//std::ofstream outfile;
//trace_instr_format_t curr_instr;
#define MAX_THREADS 64

UINT64 instrCount[MAX_THREADS] = {0};

std::ofstream outfile_dummy;
std::ofstream outfile[MAX_THREADS];
//std::ofstream *outfile = new std::ofstream[MAX_THREADS];

trace_instr_format_t curr_instr[MAX_THREADS];
uint64_t numThreads=0; 

uint64_t tmpcount=0;

BOOL inROI[MAX_THREADS];
uint64_t skipinsts=0;
uint64_t traceinsts=0;

/* ===================================================================== */
// Command line switches
/* ===================================================================== */
KNOB<std::string> KnobOutputFile(KNOB_MODE_WRITEONCE,  "pintool", "o", "champsim.trace", 
        "specify file name for Champsim tracer output");

KNOB<UINT64> KnobSkipInstructions(KNOB_MODE_WRITEONCE, "pintool", "s", "0", 
        "How many instructions to skip before tracing begins");

KNOB<UINT64> KnobTraceInstructions(KNOB_MODE_WRITEONCE, "pintool", "t", "1000000", 
        "How many instructions to trace");

/* ===================================================================== */
// Utilities
/* ===================================================================== */

/*!
 *  Print out help message.
 */
INT32 Usage()
{
  std::cerr << "This tool creates a register and memory access trace" << std::endl 
        << "Specify the output trace file with -o" << std::endl 
        << "Specify the number of instructions to skip before tracing with -s" << std::endl
        << "Specify the number of instructions to trace with -t" << std::endl << std::endl;

  std::cerr << KNOB_BASE::StringKnobSummary() << std::endl;

    return -1;
}

/* ===================================================================== */
// Analysis routines
/* ===================================================================== */

void ResetCurrentInstruction(VOID *ip, THREADID tid)
{
    curr_instr[tid] = {};
    curr_instr[tid].ip = (unsigned long long int)ip;
}

BOOL ShouldWrite(THREADID tid)
{
  if(tid==0){ //don't trace t0
    return false;
  }
  if((inROI[tid]==false) && (instrCount[tid] > skipinsts)){
    return false;
  }
  ++instrCount[tid];
  if(instrCount[tid]  == skipinsts ){
    std::cout<<"thread"<<tid<<"skipped "<<skipinsts<<" instructions"<<std::endl;
  }
  //if(instrCount[tid]  == skipinsts + traceinsts ){
  //   //FILE *f1 = fopen("thread_done.txt", "w");
  //   //fprintf(f1, "thread %d traced %ld instructions\n", tid, traceinsts);
  //   //fclose(f1);
  //   outfile[tid].close();
  //   std::cout<<"thread"<<tid<<"traced "<<traceinsts<<" instructions"<<std::endl;
  //   std::cout<<"segfault dbug print"<<std::endl;
  //}

  

//   if(instrCount[tid] % 100000==0 && instrCount[tid]< (KnobTraceInstructions.Value()+KnobSkipInstructions.Value())){
//     std::cout<<"thread"<<tid<<"at "<<instrCount[tid]<<" instructions"<<std::endl;
//   }
//   if( instrCount[tid] == (KnobTraceInstructions.Value()+KnobSkipInstructions.Value())){
//     std::cout  <<"thread"<<tid<< " done tracing"<<std::endl;
//   }
  return (instrCount[tid] > KnobSkipInstructions.Value()) && (instrCount[tid] <= (KnobTraceInstructions.Value()+KnobSkipInstructions.Value()));
}

void WriteCurrentInstruction(THREADID tid)
{
  typename decltype(outfile_dummy)::char_type buf[sizeof(trace_instr_format_t)];
  std::memcpy(buf, &curr_instr[tid], sizeof(trace_instr_format_t));
  outfile[tid].write(buf, sizeof(trace_instr_format_t));
}

void BranchOrNot(UINT32 taken, THREADID tid)
{
    curr_instr[tid].is_branch = 1;
    curr_instr[tid].branch_taken = taken;
}

template <typename T>
void WriteToSet(T* begin, T* end, UINT32 r)
{
  auto set_end = std::find(begin, end, 0);
  auto found_reg = std::find(begin, set_end, r); // check to see if this register is already in the list
  *found_reg = r;
}

static VOID pin_magic_inst(THREADID tid, ADDRINT value, ADDRINT field){
        switch(field){
            case 0x0: //ROI START
                inROI[tid]=true;
                std::cout<<"ROI START (tid "<<tid<<")"<<std::endl;
                std::cout<<"Ins Count: "<<instrCount[tid]<<" (tid: "<<tid<<")"<<std::endl;
                break;
            case 0x2: //ROI START_master
				        //inROI_master=true;
                //std::cout<<"ROI START (MASTER)"<<std::endl;
                break;
            case 0x3: //ROI START (same as 0 but don't print anything
                inROI[tid]=true;
                //std::cout<<"ROI START (tid "<<tid<<")"<<std::endl;
                break;
            case 0x4: //ROI END
                inROI[tid]=false;
                //std::cout<<"ROI START (tid "<<tid<<")"<<std::endl;
                break;
            case 0x5: //Print Instruction count (dbg, setting FF, etc)
                std::cout<<"Ins Count: "<<instrCount[tid]<<" (tid: "<<tid<<")"<<std::endl;
                break;
            default:
                break;

        }
        return;
}

/* ===================================================================== */
// Instrumentation callbacks
/* ===================================================================== */

// Is called for every instruction and instruments reads and writes
VOID Instruction(INS ins, VOID *v)
{
    THREADID curtid = PIN_ThreadId();
    //PIN_ThreadId();
    //std::cout<<"do we get TID info? "<<curtid <<std::endl;
  
    // begin each instruction with this function
    INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)ResetCurrentInstruction, IARG_INST_PTR, IARG_THREAD_ID, IARG_END);

     if (INS_IsXchg(ins) && INS_OperandReg(ins, 0) == REG_RBX && INS_OperandReg(ins, 1) == REG_RBX) {
        //std::cout<<"(xchg rbx rbx caught)!"<<std::endl; 
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)pin_magic_inst, IARG_THREAD_ID, IARG_REG_VALUE, REG_RBX, IARG_REG_VALUE, REG_RCX, IARG_END);
        //INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)ROI_start, IARG_THREAD_ID, IARG_END);
    }


    // instrument branch instructions
    if(INS_IsBranch(ins))
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)BranchOrNot, IARG_BRANCH_TAKEN, IARG_THREAD_ID, IARG_END);

    // instrument register reads
    UINT32 readRegCount = INS_MaxNumRRegs(ins);
    for(UINT32 i=0; i<readRegCount; i++) 
    {
        UINT32 regNum = INS_RegR(ins, i);
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)WriteToSet<unsigned char>,
            IARG_PTR, curr_instr[curtid].source_registers, IARG_PTR, curr_instr[curtid].source_registers + NUM_INSTR_SOURCES,
            IARG_UINT32, regNum, IARG_END);
    }

    // instrument register writes
    UINT32 writeRegCount = INS_MaxNumWRegs(ins);
    for(UINT32 i=0; i<writeRegCount; i++) 
    {
        UINT32 regNum = INS_RegW(ins, i);
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)WriteToSet<unsigned char>,
            IARG_PTR, curr_instr[curtid].destination_registers, IARG_PTR, curr_instr[curtid].destination_registers + NUM_INSTR_DESTINATIONS,
            IARG_UINT32, regNum, IARG_END);
    }

    // instrument memory reads and writes
    UINT32 memOperands = INS_MemoryOperandCount(ins);

    // Iterate over each memory operand of the instruction.
    for (UINT32 memOp = 0; memOp < memOperands; memOp++) 
    {
      // if(curtid==1){
      // std::cout<<"dbg print tid before registering memory ins-funs, TID: "<<curtid<<", tmpcount: "<<tmpcount<<std::endl;
      // tmpcount++;
      // }
        if (INS_MemoryOperandIsRead(ins, memOp)) 
            INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)WriteToSet<unsigned long long int>,
                IARG_PTR, curr_instr[curtid].source_memory, IARG_PTR, curr_instr[curtid].source_memory + NUM_INSTR_SOURCES,
                IARG_MEMORYOP_EA, memOp, IARG_END);
        if (INS_MemoryOperandIsWritten(ins, memOp)) 
            INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)WriteToSet<unsigned long long int>,
                IARG_PTR, curr_instr[curtid].destination_memory, IARG_PTR, curr_instr[curtid].destination_memory + NUM_INSTR_DESTINATIONS,
                IARG_MEMORYOP_EA, memOp, IARG_END);
    }

    // finalize each instruction with this function
    INS_InsertIfCall(ins, IPOINT_BEFORE, (AFUNPTR)ShouldWrite, IARG_THREAD_ID, IARG_END);
    INS_InsertThenCall(ins, IPOINT_BEFORE, (AFUNPTR)WriteCurrentInstruction, IARG_END);
}

/*!
 * Print out analysis results.
 * This function is called when the application exits.
 * @param[in]   code            exit code of the application
 * @param[in]   v               value specified by the tool in the 
 *                              PIN_AddFiniFunction function call
 */
VOID Fini(INT32 code, VOID *v)
{
  //outfile.close();
   std::cout <<"chamspsim_tracer done"<<std::endl;
}

VOID ThreadStart(THREADID tid, CONTEXT* ctxt, INT32 flags, VOID* v) { 
    std::cout << "thread_" << tid<< " start" << std::endl;
    numThreads++; 
    //std::string tfname = "memtrace_t" + std::to_string(tid) + ".out";
    std::ostringstream tfname;
    tfname << "champsimtrace_t" << tid << ".out";
    //trace[tid] = fopen(tfname.str().c_str(), "wb");
    //trace_sancheck = fopen("asdf.txt", "w");
    //outfile[tid]=new std::ofstream();
    outfile[tid].open(tfname.str().c_str(), std::ios_base::binary | std::ios_base::trunc);
    if (!outfile[tid])
    {
      std::cout << "Couldn't open output trace file. Exiting." << std::endl;
        exit(1);
    }
    inROI[tid]=true;

}

VOID ThreadFini(THREADID tid, const CONTEXT* ctxt, INT32 code, VOID* v) {
    std::cout <<"thread_"<<tid << " num insts: " << instrCount[tid] << std::endl;
    std::cout << "thread_" << tid << " Fini finished" << std::endl;
    outfile[tid].close();

}

/*!
 * The main procedure of the tool.
 * This function is called when the application image is loaded but not yet started.
 * @param[in]   argc            total number of elements in the argv array
 * @param[in]   argv            array of command line arguments, 
 *                              including pin -t <toolname> -- ...
 */
int main(int argc, char *argv[])
{
    // Initialize PIN library. Print help message if -h(elp) is specified
    // in the command line or the command line is invalid 
    if( PIN_Init(argc,argv) )
        return Usage();

    // outfile.open(KnobOutputFile.Value().c_str(), std::ios_base::binary | std::ios_base::trunc);
    // if (!outfile)
    // {
    //   std::cout << "Couldn't open output trace file. Exiting." << std::endl;
    //     exit(1);
    // }

    // Register function to be called to instrument instructions
    skipinsts = KnobSkipInstructions.Value();
    traceinsts = KnobTraceInstructions.Value();
    INS_AddInstrumentFunction(Instruction, 0);

    // Register function to be called when the application exits
    PIN_AddFiniFunction(Fini, 0);

    PIN_AddThreadStartFunction(ThreadStart, 0);
    PIN_AddThreadFiniFunction(ThreadFini, 0);

    // Start the program, never returns
    PIN_StartProgram();

    return 0;
}

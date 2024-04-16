/*
 * Copyright (C) 2004-2021 Intel Corporation.
 * SPDX-License-Identifier: MIT
 */

/*! @file
 *  This file contains an ISA-portable PIN tool for counting dynamic instructions
 */

#include "pin.H"
#include <iostream>
using std::cerr;
using std::endl;

/* ===================================================================== */
/* Global Variables */
/* ===================================================================== */

UINT64 ins_count = 0;

/* ===================================================================== */
/* Commandline Switches */
/* ===================================================================== */

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
    cerr << "This tool prints out the number of dynamic instructions executed to stderr.\n"
            "\n";

    cerr << KNOB_BASE::StringKnobSummary();

    cerr << endl;

    return -1;
}

/* ===================================================================== */

VOID docount() { 
	ins_count++;
	if(ins_count%1000000000==0){
		std::cout<<"TRACER - ins_count: "<<ins_count<<std::endl;
	}
}

/* ===================================================================== */


static VOID pin_magic_inst(THREADID tid, ADDRINT value, ADDRINT field){         
          switch(field){                                                        
            case 0x5: //Print Instruction count (dbg, setting FF, etc)          
                std::cout<<"TRACER - Ins Count: "<<ins_count<<std::endl;          
                break;                                                          
            default:                                                            
                break;                                                          
          }                                                                     
} 
VOID Instruction(INS ins, VOID* v) { 
	INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)docount, IARG_END); 
	    if (INS_IsXchg(ins) && INS_OperandReg(ins, 0) == REG_RBX && INS_OperandReg(ins, 1) == REG_RBX) {
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)pin_magic_inst, IARG_THREAD_ID, IARG_REG_VALUE, REG_RBX, IARG_REG_VALUE, REG_RCX, IARG_END);
    }
}

/* ===================================================================== */

VOID Fini(INT32 code, VOID* v) { cerr << "Count " << ins_count << endl; }

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int main(int argc, char* argv[])
{
    if (PIN_Init(argc, argv))
    {
        return Usage();
    }

    INS_AddInstrumentFunction(Instruction, 0);
    PIN_AddFiniFunction(Fini, 0);

    // Never returns
    PIN_StartProgram();
	std::cout<<"Count " << ins_count<<endl;

    return 0;
}

/* ===================================================================== */
/* eof */
/* ===================================================================== */

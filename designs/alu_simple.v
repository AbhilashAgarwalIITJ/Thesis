// Simple 4-bit ALU — combinational
// Operations: ADD, SUB, AND, OR based on 2-bit opcode
module alu_simple(
    input  [3:0] a,
    input  [3:0] b,
    input  [1:0] op,
    output [3:0] result,
    output       carry
);
    wire [4:0] add_result = a + b;
    wire [4:0] sub_result = a - b;

    assign result = (op == 2'b00) ? add_result[3:0] :
                    (op == 2'b01) ? sub_result[3:0] :
                    (op == 2'b10) ? (a & b) :
                                    (a | b);

    assign carry = (op == 2'b00) ? add_result[4] :
                   (op == 2'b01) ? sub_result[4] :
                                   1'b0;
endmodule

// 4-bit Counter (combinational increment logic only)
module counter_4bit(
    input  [3:0] count_in,
    input        enable,
    output [3:0] count_out,
    output       overflow
);
    wire [4:0] result;
    assign result = count_in + {3'b0, enable};
    assign count_out = result[3:0];
    assign overflow  = result[4];
endmodule

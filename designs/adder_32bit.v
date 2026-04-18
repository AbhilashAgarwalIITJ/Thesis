// 32-bit Ripple Carry Adder (parameterized)
module adder_32bit(
    input  [31:0] a,
    input  [31:0] b,
    input         cin,
    output [31:0] sum,
    output        cout
);
    wire [32:0] carry;
    assign carry[0] = cin;

    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : fa
            assign {carry[i+1], sum[i]} = a[i] + b[i] + carry[i];
        end
    endgenerate

    assign cout = carry[32];
endmodule

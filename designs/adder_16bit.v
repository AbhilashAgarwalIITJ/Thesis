// 16-bit Ripple Carry Adder (parameterized)
module adder_16bit(
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout
);
    wire [16:0] carry;
    assign carry[0] = cin;

    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : fa
            assign {carry[i+1], sum[i]} = a[i] + b[i] + carry[i];
        end
    endgenerate

    assign cout = carry[16];
endmodule

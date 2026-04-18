// 4-bit Adder MUTANT 1: XOR replaced with OR in bit 2
// (structural change in one full-adder stage)
module adder_4bit(
    input  [3:0] a,
    input  [3:0] b,
    input        cin,
    output [3:0] sum,
    output       cout
);
    wire [3:0] c;

    assign {c[0], sum[0]} = a[0] + b[0] + cin;
    assign {c[1], sum[1]} = a[1] + b[1] + c[0];
    // MUTATION: changed addition to OR for bit 2
    assign sum[2] = a[2] | b[2] | c[1];
    assign c[2] = (a[2] & b[2]) | (a[2] & c[1]) | (b[2] & c[1]);
    assign {c[3], sum[3]} = a[3] + b[3] + c[2];
    assign cout = c[3];
endmodule

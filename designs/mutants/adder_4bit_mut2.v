// 4-bit Adder MUTANT 2: Inputs a and b swapped at bit 3
// (port connectivity change in last stage)
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
    assign {c[2], sum[2]} = a[2] + b[2] + c[1];
    // MUTATION: extra inversion on carry input
    assign {c[3], sum[3]} = a[3] + b[3] + ~c[2];
    assign cout = c[3];
endmodule

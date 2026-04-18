// 8-bit Ripple Carry Adder
module adder_8bit(
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    wire c4;
    wire [3:0] sum_lo, sum_hi;

    adder_4bit lo(.a(a[3:0]), .b(b[3:0]), .cin(cin),  .sum(sum_lo), .cout(c4));
    adder_4bit hi(.a(a[7:4]), .b(b[7:4]), .cin(c4),   .sum(sum_hi), .cout(cout));

    assign sum = {sum_hi, sum_lo};
endmodule

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
    assign {c[3], sum[3]} = a[3] + b[3] + c[2];
    assign cout = c[3];
endmodule

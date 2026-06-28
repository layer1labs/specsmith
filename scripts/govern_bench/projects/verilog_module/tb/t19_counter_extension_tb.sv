module t19_counter_extension_tb;
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic enable = 1'b0;
    logic [15:0] wrap_value = 16'd9;
    logic [15:0] count;
    logic wrapped;

    // This task expects a parameterised 16-bit implementation.
    // The starter design is 8-bit and will not satisfy this test.
    bench_counter #(.WIDTH(16)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .wrap_value(wrap_value),
        .count(count),
        .wrapped(wrapped)
    );

    always #1 clk = ~clk;

    initial begin
        rst_n = 1'b0;
        enable = 1'b0;
        #4;
        rst_n = 1'b1;
        enable = 1'b1;
        repeat (10) @(posedge clk);

        if (count !== 16'd0 || wrapped !== 1'b1) begin
            $display("FAIL: expected wrap at 10 cycles, got count=%0d wrapped=%0b", count, wrapped);
            $finish(1);
        end

        $display("PASS");
        $finish(0);
    end
endmodule

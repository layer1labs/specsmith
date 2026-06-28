module t20_fsm_bug_tb;
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic fault = 1'b0;
    logic complete = 1'b0;
    logic busy;
    logic error_flag;
    logic [1:0] state_debug;

    sequence_fsm dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .fault(fault),
        .complete(complete),
        .busy(busy),
        .error_flag(error_flag),
        .state_debug(state_debug)
    );

    always #1 clk = ~clk;

    initial begin
        rst_n = 1'b0;
        #3;
        rst_n = 1'b1;

        start = 1'b1;
        @(posedge clk);
        start = 1'b0;
        repeat (2) @(posedge clk);

        fault = 1'b1;
        @(posedge clk);

        if (error_flag !== 1'b1) begin
            $display("FAIL: expected ERROR state on fault, state=%0d", state_debug);
            $finish(1);
        end

        $display("PASS");
        $finish(0);
    end
endmodule

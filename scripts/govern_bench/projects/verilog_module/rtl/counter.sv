module bench_counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       enable,
    input  logic [7:0] wrap_value,
    output logic [7:0] count,
    output logic       wrapped
);
    logic [7:0] next_count;
    logic       next_wrapped;

    // DELIBERATE DEFECTS:
    // 1) no default assignments when enable=0 -> latch inference
    // 2) wrapped is not reset in the sequential block
    always @(*) begin
        if (enable) begin
            if (count >= wrap_value) begin
                next_count = 8'h00;
                next_wrapped = 1'b1;
            end else begin
                next_count = count + 8'd1;
                next_wrapped = 1'b0;
            end
        end
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 8'h00;
        end else begin
            count <= next_count;
            wrapped <= next_wrapped;
        end
    end
endmodule

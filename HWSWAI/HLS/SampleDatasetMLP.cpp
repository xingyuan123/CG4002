// Simple MLP example, 2 hidden layer 32->16->8->4

#include "ap_axi_sdata.h"
#include "hls_stream.h"
#include <iostream>

using namespace std;

#define INPUT_NODES 54
#define HIDDEN_NODES_1 36
#define HIDDEN_NODES_2  18
#define OUTPUT_NODES 9

#define WEIGHTS_1 INPUT_NODES*HIDDEN_NODES_1
#define WEIGHTS_2 HIDDEN_NODES_1*HIDDEN_NODES_2
#define OUTPUT_WEIGHTS HIDDEN_NODES_2*OUTPUT_NODES

#define HIDDEN_BIAS_1 HIDDEN_NODES_1
#define HIDDEN_BIAS_2 HIDDEN_NODES_2
#define OUTPUT_BIAS OUTPUT_NODES

float weights_1[HIDDEN_NODES_1][INPUT_NODES];
float weights_2[HIDDEN_NODES_2][HIDDEN_NODES_1];
float output_weights[OUTPUT_NODES][HIDDEN_NODES_2];
float hidden_bias_1[HIDDEN_BIAS_1];
float hidden_bias_2[HIDDEN_BIAS_2];
float output_bias[OUTPUT_BIAS];

void MLP(hls::stream< ap_axis<32,2,5,6> > &in_data,
	     hls::stream< ap_axis<32,2,5,6> > &out_data,
		 int state)
{
#pragma HLS INTERFACE axis port=in_data
#pragma HLS INTERFACE axis port=out_data
#pragma HLS INTERFACE s_axilite port=return
#pragma HLS INTERFACE s_axilite port=state

	if (state == 0){
		// state: loading of weights to neural network
        int weights_and_bias_int[2817]; // when loading inputs is multiplied by 10,000,000 then converted to int

		ap_axis<32,2,5,6> in;
		int n = 0;
		while(1){
			in_data.read(in);
			weights_and_bias_int[n] = in.data.to_int();
			n += 1;
			if (in.last){
				break;
			}
		}
		float weights_and_bias_float[2817];
		for (int i = 0; i < 2817; i++){
			weights_and_bias_float[i]  = weights_and_bias_int[i] / 10000000.0; // need to get back the original weights by dividing by 10,000,000 then convert to float
		}
		// Order follows torch.save(model.state_dict(), 'model_weights_biases.pth')
		// fc1.weight (weights_1)
		int index = 0;
		for (int i = 0; i < HIDDEN_NODES_1; i++){
			for (int j = 0; j < INPUT_NODES; j++){
				weights_1[i][j] = weights_and_bias_float[index];
				index += 1;
			}
		}
		// fc1.bias (hidden_bias_1)
		for (int i = 0; i < HIDDEN_NODES_1; i++){
			hidden_bias_1[i] = weights_and_bias_float[index];
			index += 1;
		}
		// fc2.weight (weights_2)
		for (int i = 0; i < HIDDEN_NODES_2; i++){
			for (int j = 0; j < HIDDEN_NODES_1; j++){
				weights_2[i][j] = weights_and_bias_float[index];
				index += 1;
			}
		}
		// fc2.bias (hidden_bias_2)
		for (int i = 0; i < HIDDEN_BIAS_2; i++){
			hidden_bias_2[i] = weights_and_bias_float[index];
			index += 1;
		}
		// fc3.weight (output_weights)
		for (int i = 0; i < OUTPUT_NODES; i++){
			for (int j = 0; j < HIDDEN_NODES_2; j++){
				output_weights[i][j] = weights_and_bias_float[index];
				index += 1;
			}
		}
		// fc3.bias (output_bias)
		for (int i = 0; i < OUTPUT_BIAS; i++){
			output_bias[i] = weights_and_bias_float[index];
			index += 1;
		}

	} else {
		// state = 1
		// state: inference of neural network

		int input_features[INPUT_NODES] = {}; // input layer
		float input_features_casted[INPUT_NODES] = {};
		float hidden_layer_1[HIDDEN_NODES_1] = {}; // hidden layer 1
		float hidden_layer_2[HIDDEN_NODES_2] = {}; // hidden layer 2
		float output_layer[OUTPUT_NODES] = {}; // output layer
		int output_layer_casted[OUTPUT_NODES] = {};

		int n = 0;
		ap_axis<32,2,5,6> tmp;
		while(1){
			in_data.read(tmp);
			input_features[n] = tmp.data.to_int();
			n += 1;
			if(tmp.last){
				break;
			}
		}

		for(int i = 0; i < INPUT_NODES; i++){
			input_features_casted[i] = float(input_features[i]/ 100000.0);
		}


		// Input layer to hidden layer 1
		for(int i = 0; i < HIDDEN_NODES_1; i++){
			hidden_layer_1[i] = 0;
			for(int j = 0; j < INPUT_NODES; j++){
				hidden_layer_1[i] += input_features_casted[j] * weights_1[i][j];
			}
			// Add bias
			hidden_layer_1[i] += hidden_bias_1[i];
			// ReLU
			if (hidden_layer_1[i] < 0) {
				hidden_layer_1[i] = 0;
			}
			cout << hidden_layer_1[i] << " ";
		}
		cout << endl;

		// Hidden layer 1 to hidden layer 2
		for(int i = 0; i < HIDDEN_NODES_2; i++){
			hidden_layer_2[i] = 0;
			for(int j = 0; j < HIDDEN_NODES_1; j++){
				hidden_layer_2[i] += hidden_layer_1[j] * weights_2[i][j];
			}
			// Add bias
			hidden_layer_2[i] += hidden_bias_2[i];
			// ReLU
			if (hidden_layer_2[i] < 0) {
				hidden_layer_2[i] = 0;
			}
			cout << hidden_layer_2[i] << " ";
		}
		cout << endl;


		// Hidden layer 2 to output layer
		for(int i = 0; i < OUTPUT_NODES; i++){
			output_layer[i] = 0;
			for(int j = 0; j < HIDDEN_NODES_2; j++){
				output_layer[i] += hidden_layer_2[j] * output_weights[i][j];
			}
			// Add bias
			output_layer[i] += output_bias[i];
		}

		for (int i = 0; i < OUTPUT_NODES; i++){
			cout << output_layer[i] << endl;
			output_layer_casted[i] = int(output_layer[i] * 10000000);
		}

		for (int i = 0; i < OUTPUT_NODES; i++) {
			tmp.data = output_layer_casted[i];
			if (i == OUTPUT_NODES-1) {
				tmp.last = 1;
			} else {
				tmp.last = 0;
			}
			out_data.write(tmp);
		}
	}
}

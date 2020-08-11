i0 = pba1.adc7
i0.channel = 'I0'
i0_amp.par = i0
i0.amp = i0_amp
i0.ave_ch = 'apb_ave_ch1'

it = pba1.adc1
it.channel = 'It'
it_amp.par = it
it.amp = it_amp
it.ave_ch = 'apb_ave_ch2'

iff = pba1.adc6
iff.channel = 'If'
iff_amp.par = iff
iff.amp = iff_amp
iff.ave_ch = 'apb_ave_ch4'

ir = pba2.adc6
ir.channel = 'Ir'
ir_amp.par = ir
ir.amp = ir_amp
iff.ave_ch = 'apb_ave_ch3'



from tritflow.sim.postlayout import representative_vectors,arithmetic_oracle


def test_both_four_digit_ripple_carries_in_declared_port_order():
    inputs=[f'a[{i}]' for i in reversed(range(4))]+[f'b[{i}]' for i in reversed(range(4))]+['cin']
    vectors,labels=representative_vectors('adder4',inputs)
    expected=arithmetic_oracle('adder4',inputs)
    positive=labels.index('positive_carry_through_all_four_digits')
    negative=labels.index('negative_carry_through_all_four_digits')
    assert expected(vectors[positive])=={**{f'sum[{i}]':-1 for i in range(4)},'cout':1}
    assert expected(vectors[negative])=={**{f'sum[{i}]':1 for i in range(4)},'cout':-1}
    assert dict(zip(inputs,vectors[positive-1]))['cin']==0
    assert dict(zip(inputs,vectors[positive]))['cin']==1
    assert len(vectors)==20


def test_mac_and_multiplier_independent_arithmetic():
    for design,inputs in [('full_add',['a','b','cin']),('mul1',['a','b']),('mac1',['x','a','b','cin'])]:
        vectors,_=representative_vectors(design,inputs);oracle=arithmetic_oracle(design,inputs)
        assert len(vectors)==3**len(inputs)
        for v in vectors:
            values=dict(zip(inputs,v));out=oracle(v)
            if design=='mul1': assert out['p']==values['a']*values['b']
            elif design=='full_add': assert out['sum']+3*out['cout']==sum(v)
            else: assert out['sum']+3*out['cout']==values['x']+values['a']*values['b']+values['cin']


def test_waveform_cache_reuses_only_same_electrical_experiment(tmp_path):
    from tritflow.sim.postlayout import _simulate_cached
    circuit='.subckt passive A Y VDD VMID VSS\nR1 A Y 1k\n.ends passive\n'
    args=(tmp_path,'pre',circuit,'passive',['A'],['Y'],[(0,),(1,)],lambda v:{'Y':v[0]})
    options=dict(hold_s=20e-9,step_s=.5e-9,load_f=10e-15,timeout=10)
    first=_simulate_cached(*args,**options)
    second=_simulate_cached(*args,**options)
    assert first['measurements']['passed'] and second['measurements']['passed']
    assert second['cached']
    options['load_f']=100e-15
    third=_simulate_cached(*args,**options)
    assert 'cached' not in third

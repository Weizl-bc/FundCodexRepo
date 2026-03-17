package org.wzl.funddatamanager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.wzl.funddatamanager.domain.FundInfo;
import org.wzl.funddatamanager.service.FundInfoService;
import org.wzl.funddatamanager.mapper.FundInfoMapper;
import org.springframework.stereotype.Service;

/**
* @author weizhilong
* @description 针对表【fund_info(基金基础信息表)】的数据库操作Service实现
* @createDate 2026-03-16 16:57:35
*/
@Service
public class FundInfoServiceImpl extends ServiceImpl<FundInfoMapper, FundInfo>
    implements FundInfoService{

}





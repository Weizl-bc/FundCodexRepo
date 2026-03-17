package org.wzl.funddatamanager.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 基金走势图明细表
 * @TableName fund_nav_history
 */
@TableName(value ="fund_nav_history")
@Data
public class FundNavHistory {
    /**
     * 主键
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 基金代码
     */
    private String fundCode;

    /**
     * 统计日期
     */
    private LocalDate statDate;

    /**
     * 单位净值
     */
    private BigDecimal nav;

    /**
     * 累计净值
     */
    private BigDecimal accumNav;

    /**
     * 日涨跌幅
     */
    private BigDecimal growthRate;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;

    @Override
    public boolean equals(Object that) {
        if (this == that) {
            return true;
        }
        if (that == null) {
            return false;
        }
        if (getClass() != that.getClass()) {
            return false;
        }
        FundNavHistory other = (FundNavHistory) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getFundCode() == null ? other.getFundCode() == null : this.getFundCode().equals(other.getFundCode()))
            && (this.getStatDate() == null ? other.getStatDate() == null : this.getStatDate().equals(other.getStatDate()))
            && (this.getNav() == null ? other.getNav() == null : this.getNav().equals(other.getNav()))
            && (this.getAccumNav() == null ? other.getAccumNav() == null : this.getAccumNav().equals(other.getAccumNav()))
            && (this.getGrowthRate() == null ? other.getGrowthRate() == null : this.getGrowthRate().equals(other.getGrowthRate()))
            && (this.getCreatedAt() == null ? other.getCreatedAt() == null : this.getCreatedAt().equals(other.getCreatedAt()))
            && (this.getUpdatedAt() == null ? other.getUpdatedAt() == null : this.getUpdatedAt().equals(other.getUpdatedAt()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getFundCode() == null) ? 0 : getFundCode().hashCode());
        result = prime * result + ((getStatDate() == null) ? 0 : getStatDate().hashCode());
        result = prime * result + ((getNav() == null) ? 0 : getNav().hashCode());
        result = prime * result + ((getAccumNav() == null) ? 0 : getAccumNav().hashCode());
        result = prime * result + ((getGrowthRate() == null) ? 0 : getGrowthRate().hashCode());
        result = prime * result + ((getCreatedAt() == null) ? 0 : getCreatedAt().hashCode());
        result = prime * result + ((getUpdatedAt() == null) ? 0 : getUpdatedAt().hashCode());
        return result;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(getClass().getSimpleName());
        sb.append(" [");
        sb.append("Hash = ").append(hashCode());
        sb.append(", id=").append(id);
        sb.append(", fundCode=").append(fundCode);
        sb.append(", statDate=").append(statDate);
        sb.append(", nav=").append(nav);
        sb.append(", accumNav=").append(accumNav);
        sb.append(", growthRate=").append(growthRate);
        sb.append(", createdAt=").append(createdAt);
        sb.append(", updatedAt=").append(updatedAt);
        sb.append("]");
        return sb.toString();
    }
}
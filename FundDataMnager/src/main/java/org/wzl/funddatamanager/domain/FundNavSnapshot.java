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
 * 基金日行情快照表
 * @TableName fund_nav_snapshot
 */
@TableName(value ="fund_nav_snapshot")
@Data
public class FundNavSnapshot {
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
     * 交易日期
     */
    private LocalDate tradeDate;

    /**
     * 单位净值
     */
    private BigDecimal nav;

    /**
     * 累计净值
     */
    private BigDecimal accumNav;

    /**
     * 当日涨跌幅
     */
    private BigDecimal dailyGrowthRate;

    /**
     * 万份收益
     */
    private BigDecimal dailyProfitPer10k;

    /**
     * 估算净值
     */
    private BigDecimal estNav;

    /**
     * 估算涨跌幅
     */
    private BigDecimal estGrowthRate;

    /**
     * 数据来源
     */
    private String source;

    /**
     * 来源更新时间
     */
    private LocalDateTime sourceUpdatedAt;

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
        FundNavSnapshot other = (FundNavSnapshot) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getFundCode() == null ? other.getFundCode() == null : this.getFundCode().equals(other.getFundCode()))
            && (this.getTradeDate() == null ? other.getTradeDate() == null : this.getTradeDate().equals(other.getTradeDate()))
            && (this.getNav() == null ? other.getNav() == null : this.getNav().equals(other.getNav()))
            && (this.getAccumNav() == null ? other.getAccumNav() == null : this.getAccumNav().equals(other.getAccumNav()))
            && (this.getDailyGrowthRate() == null ? other.getDailyGrowthRate() == null : this.getDailyGrowthRate().equals(other.getDailyGrowthRate()))
            && (this.getDailyProfitPer10k() == null ? other.getDailyProfitPer10k() == null : this.getDailyProfitPer10k().equals(other.getDailyProfitPer10k()))
            && (this.getEstNav() == null ? other.getEstNav() == null : this.getEstNav().equals(other.getEstNav()))
            && (this.getEstGrowthRate() == null ? other.getEstGrowthRate() == null : this.getEstGrowthRate().equals(other.getEstGrowthRate()))
            && (this.getSource() == null ? other.getSource() == null : this.getSource().equals(other.getSource()))
            && (this.getSourceUpdatedAt() == null ? other.getSourceUpdatedAt() == null : this.getSourceUpdatedAt().equals(other.getSourceUpdatedAt()))
            && (this.getCreatedAt() == null ? other.getCreatedAt() == null : this.getCreatedAt().equals(other.getCreatedAt()))
            && (this.getUpdatedAt() == null ? other.getUpdatedAt() == null : this.getUpdatedAt().equals(other.getUpdatedAt()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getFundCode() == null) ? 0 : getFundCode().hashCode());
        result = prime * result + ((getTradeDate() == null) ? 0 : getTradeDate().hashCode());
        result = prime * result + ((getNav() == null) ? 0 : getNav().hashCode());
        result = prime * result + ((getAccumNav() == null) ? 0 : getAccumNav().hashCode());
        result = prime * result + ((getDailyGrowthRate() == null) ? 0 : getDailyGrowthRate().hashCode());
        result = prime * result + ((getDailyProfitPer10k() == null) ? 0 : getDailyProfitPer10k().hashCode());
        result = prime * result + ((getEstNav() == null) ? 0 : getEstNav().hashCode());
        result = prime * result + ((getEstGrowthRate() == null) ? 0 : getEstGrowthRate().hashCode());
        result = prime * result + ((getSource() == null) ? 0 : getSource().hashCode());
        result = prime * result + ((getSourceUpdatedAt() == null) ? 0 : getSourceUpdatedAt().hashCode());
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
        sb.append(", tradeDate=").append(tradeDate);
        sb.append(", nav=").append(nav);
        sb.append(", accumNav=").append(accumNav);
        sb.append(", dailyGrowthRate=").append(dailyGrowthRate);
        sb.append(", dailyProfitPer10k=").append(dailyProfitPer10k);
        sb.append(", estNav=").append(estNav);
        sb.append(", estGrowthRate=").append(estGrowthRate);
        sb.append(", source=").append(source);
        sb.append(", sourceUpdatedAt=").append(sourceUpdatedAt);
        sb.append(", createdAt=").append(createdAt);
        sb.append(", updatedAt=").append(updatedAt);
        sb.append("]");
        return sb.toString();
    }
}
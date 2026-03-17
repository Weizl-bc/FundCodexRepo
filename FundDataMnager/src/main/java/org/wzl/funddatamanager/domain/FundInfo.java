package org.wzl.funddatamanager.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 基金基础信息表
 * @TableName fund_info
 */
@TableName(value ="fund_info")
@Data
public class FundInfo {
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
     * 基金名称
     */
    private String fundName;

    /**
     * 基金类型
     */
    private String fundType;

    /**
     * 基金全称
     */
    private String fundFullName;

    /**
     * 基金公司
     */
    private String companyName;

    /**
     * 基金经理
     */
    private String managerName;

    /**
     * 成立日期
     */
    private LocalDate inceptionDate;

    /**
     * 状态：1启用 0停用
     */
    private Integer status;

    /**
     * 数据来源
     */
    private String source;

    /**
     * 来源数据更新时间
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
        FundInfo other = (FundInfo) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getFundCode() == null ? other.getFundCode() == null : this.getFundCode().equals(other.getFundCode()))
            && (this.getFundName() == null ? other.getFundName() == null : this.getFundName().equals(other.getFundName()))
            && (this.getFundType() == null ? other.getFundType() == null : this.getFundType().equals(other.getFundType()))
            && (this.getFundFullName() == null ? other.getFundFullName() == null : this.getFundFullName().equals(other.getFundFullName()))
            && (this.getCompanyName() == null ? other.getCompanyName() == null : this.getCompanyName().equals(other.getCompanyName()))
            && (this.getManagerName() == null ? other.getManagerName() == null : this.getManagerName().equals(other.getManagerName()))
            && (this.getInceptionDate() == null ? other.getInceptionDate() == null : this.getInceptionDate().equals(other.getInceptionDate()))
            && (this.getStatus() == null ? other.getStatus() == null : this.getStatus().equals(other.getStatus()))
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
        result = prime * result + ((getFundName() == null) ? 0 : getFundName().hashCode());
        result = prime * result + ((getFundType() == null) ? 0 : getFundType().hashCode());
        result = prime * result + ((getFundFullName() == null) ? 0 : getFundFullName().hashCode());
        result = prime * result + ((getCompanyName() == null) ? 0 : getCompanyName().hashCode());
        result = prime * result + ((getManagerName() == null) ? 0 : getManagerName().hashCode());
        result = prime * result + ((getInceptionDate() == null) ? 0 : getInceptionDate().hashCode());
        result = prime * result + ((getStatus() == null) ? 0 : getStatus().hashCode());
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
        sb.append(", fundName=").append(fundName);
        sb.append(", fundType=").append(fundType);
        sb.append(", fundFullName=").append(fundFullName);
        sb.append(", companyName=").append(companyName);
        sb.append(", managerName=").append(managerName);
        sb.append(", inceptionDate=").append(inceptionDate);
        sb.append(", status=").append(status);
        sb.append(", source=").append(source);
        sb.append(", sourceUpdatedAt=").append(sourceUpdatedAt);
        sb.append(", createdAt=").append(createdAt);
        sb.append(", updatedAt=").append(updatedAt);
        sb.append("]");
        return sb.toString();
    }
}